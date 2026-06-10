"""
Alert engine — Module 5 (Phase 4).

Evaluates alert rules, creates Alert records, and dispatches
notifications via dashboard (Redis), WhatsApp, and email channels.
Extends the existing Alert model without modifying it.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.config import Settings
from shared.database.alert_rule_models import AlertRule
from shared.database.analytics_models import AnalyticsSession, FootfallDailyCamera
from shared.database.models import Alert
from shared.database.tenant_models import Camera, Store

logger = logging.getLogger(__name__)

ALERT_COOLDOWN_MINUTES = 30  # Default cooldown between same-type alerts


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AlertEngine:
    """
    Evaluates and dispatches alerts for a specific brand.

    Designed to be called from:
    - Ingest endpoints (on new session data)
    - Scheduled health checks (camera offline detection)
    - Recognition pipeline (VIP/watchlist detection)
    """

    def __init__(
        self,
        db: Session,
        settings: Settings,
        brand_id: uuid.UUID,
    ) -> None:
        self.db = db
        self.settings = settings
        self.brand_id = brand_id

    # ------------------------------------------------------------------
    # Rule loading
    # ------------------------------------------------------------------

    def _load_rules(
        self,
        alert_type: str,
        store_id: Optional[str] = None,
    ) -> list[AlertRule]:
        stmt = select(AlertRule).where(
            AlertRule.brand_id == self.brand_id,
            AlertRule.alert_type == alert_type,
            AlertRule.enabled == True,
        )
        if store_id:
            stmt = stmt.where(
                (AlertRule.store_id == store_id) | (AlertRule.store_id == None)
            )
        return list(self.db.scalars(stmt).all())

    # ------------------------------------------------------------------
    # Cooldown check
    # ------------------------------------------------------------------

    def _is_in_cooldown(
        self,
        alert_type: str,
        store_id: Optional[str],
        cooldown_minutes: int = ALERT_COOLDOWN_MINUTES,
    ) -> bool:
        cutoff = _utcnow() - timedelta(minutes=cooldown_minutes)
        stmt = select(func.count()).where(
            Alert.brand_id == self.brand_id,
            Alert.alert_type == alert_type,
            Alert.created_at >= cutoff,
        )
        if store_id:
            stmt = stmt.where(Alert.store_id == store_id)
        count = self.db.scalar(stmt) or 0
        return count > 0

    # ------------------------------------------------------------------
    # Alert creation
    # ------------------------------------------------------------------

    def _create_alert(
        self,
        *,
        alert_type: str,
        store_id: Optional[str],
        message: str,
        payload: dict[str, Any],
        camera_id: Optional[str] = None,
        rule_id: Optional[uuid.UUID] = None,
    ) -> Alert:
        alert = Alert(
            brand_id=self.brand_id,
            store_id=store_id or "",
            alert_type=alert_type,
            message=message,
            payload=payload,
            acknowledged=False,
        )
        # Phase 4 extended columns (safe — added by migration)
        if camera_id is not None:
            try:
                alert.camera_id = camera_id  # type: ignore[attr-defined]
            except Exception:
                pass
        if rule_id is not None:
            try:
                alert.rule_id = rule_id  # type: ignore[attr-defined]
            except Exception:
                pass
        self.db.add(alert)
        self.db.flush()
        return alert

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, alert: Alert, rule: AlertRule) -> None:
        """Fan out alert to configured channels."""
        channels = list(rule.channels or [])
        recipients = list(rule.recipients or [])

        # Dashboard — publish to Redis
        if "dashboard" in channels or not channels:
            self._publish_dashboard(alert)

        # WhatsApp
        if "whatsapp" in channels:
            self._send_whatsapp(alert, recipients)

        # Email
        if "email" in channels:
            self._send_email(alert, recipients)

    def _publish_dashboard(self, alert: Alert) -> None:
        from backend_core.services.realtime_publisher import get_publisher
        publisher = get_publisher(self.settings.redis_url)
        publisher.publish_event(
            brand_id=self.brand_id,
            store_id=alert.store_id,
            event_type="alert_generated",
            payload={
                "alert_id": str(alert.id),
                "alert_type": alert.alert_type,
                "message": alert.message,
                "store_id": alert.store_id,
            },
        )

    def _send_whatsapp(self, alert: Alert, recipients: list[str]) -> None:
        if not recipients:
            return
        try:
            from backend_core.services.whatsapp.factory import get_whatsapp_provider
            provider = get_whatsapp_provider(self.settings)
            for r in recipients:
                if r.startswith("+") or r.lstrip("+").isdigit():
                    provider.send_text(
                        to=r,
                        message=f"🚨 Alert [{alert.alert_type}]\n{alert.message}\nStore: {alert.store_id}",
                    )
        except Exception as exc:
            logger.warning("WhatsApp alert failed: %s", exc)

    def _send_email(self, alert: Alert, recipients: list[str]) -> None:
        if not recipients or not self.settings.smtp_host:
            return
        try:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(
                f"Alert Type: {alert.alert_type}\n\n{alert.message}\n\nStore: {alert.store_id}"
            )
            msg["Subject"] = f"[Orzen Vision] Alert: {alert.alert_type}"
            msg["From"] = self.settings.smtp_from_address
            msg["To"] = ", ".join(recipients)
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                server.starttls()
                if self.settings.smtp_user:
                    server.login(self.settings.smtp_user, self.settings.smtp_password or "")
                server.sendmail(self.settings.smtp_from_address, recipients, msg.as_string())
        except Exception as exc:
            logger.warning("Email alert failed: %s", exc)

    # ------------------------------------------------------------------
    # Alert type evaluators
    # ------------------------------------------------------------------

    def check_vip_detected(
        self, store_id: str, person_id: str, camera_id: Optional[str] = None
    ) -> Optional[Alert]:
        rules = self._load_rules("vip_detected", store_id)
        if not rules:
            return None
        rule = rules[0]
        if self._is_in_cooldown("vip_detected", store_id, cooldown_minutes=5):
            return None

        alert = self._create_alert(
            alert_type="vip_detected",
            store_id=store_id,
            message=f"VIP visitor detected at {camera_id or 'store'} (ID: {person_id})",
            payload={"person_id": person_id, "camera_id": camera_id},
            camera_id=camera_id,
            rule_id=rule.id,
        )
        self.db.commit()
        self._dispatch(alert, rule)
        return alert

    def check_watchlist_detected(
        self,
        store_id: str,
        person_id: str,
        camera_id: Optional[str] = None,
        watchlist_id: Optional[str] = None,
    ) -> Optional[Alert]:
        rules = self._load_rules("watchlist_detected", store_id)
        if not rules:
            return None
        rule = rules[0]

        alert = self._create_alert(
            alert_type="watchlist_detected",
            store_id=store_id,
            message=f"Watchlist person detected: {person_id}",
            payload={"person_id": person_id, "watchlist_id": watchlist_id, "camera_id": camera_id},
            camera_id=camera_id,
            rule_id=rule.id,
        )
        self.db.commit()
        self._dispatch(alert, rule)
        return alert

    def check_camera_offline(
        self, store_id: str, camera_id: str, offline_seconds: float
    ) -> Optional[Alert]:
        rules = self._load_rules("camera_offline", store_id)
        if not rules:
            return None

        for rule in rules:
            threshold = rule.threshold or 300  # 5 min default
            if offline_seconds >= threshold:
                if self._is_in_cooldown("camera_offline", store_id, cooldown_minutes=60):
                    continue
                alert = self._create_alert(
                    alert_type="camera_offline",
                    store_id=store_id,
                    message=f"Camera {camera_id} has been offline for {int(offline_seconds)}s",
                    payload={"camera_id": camera_id, "offline_seconds": offline_seconds},
                    camera_id=camera_id,
                    rule_id=rule.id,
                )
                self.db.commit()
                self._dispatch(alert, rule)
                from backend_core.services.realtime_publisher import get_publisher
                pub = get_publisher(self.settings.redis_url)
                pub.publish_camera_health(self.brand_id, camera_id, "offline", store_id)
                return alert
        return None

    def check_high_crowd(
        self, store_id: str, current_count: int, camera_id: Optional[str] = None
    ) -> Optional[Alert]:
        rules = self._load_rules("high_crowd", store_id)
        if not rules:
            return None

        for rule in rules:
            threshold = int(rule.threshold or 50)
            if current_count >= threshold:
                if self._is_in_cooldown("high_crowd", store_id):
                    continue
                alert = self._create_alert(
                    alert_type="high_crowd",
                    store_id=store_id,
                    message=f"High crowd alert: {current_count} visitors (threshold: {threshold})",
                    payload={"current_count": current_count, "threshold": threshold},
                    camera_id=camera_id,
                    rule_id=rule.id,
                )
                self.db.commit()
                self._dispatch(alert, rule)
                return alert
        return None

    def check_low_traffic(
        self, store_id: str, hourly_count: int
    ) -> Optional[Alert]:
        rules = self._load_rules("low_traffic", store_id)
        if not rules:
            return None

        for rule in rules:
            threshold = int(rule.threshold or 5)
            if hourly_count <= threshold:
                if self._is_in_cooldown("low_traffic", store_id, cooldown_minutes=60):
                    continue
                alert = self._create_alert(
                    alert_type="low_traffic",
                    store_id=store_id,
                    message=f"Low traffic: only {hourly_count} visitors this hour (threshold: {threshold})",
                    payload={"hourly_count": hourly_count, "threshold": threshold},
                )
                self.db.commit()
                self._dispatch(alert, rule)
                return alert
        return None
