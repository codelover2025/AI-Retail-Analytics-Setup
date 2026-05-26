import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.orm import Session

from edge_ai.recognition.face_matcher import MatchResult
from shared.config import Settings
from shared.database.models import Alert, Visitor
from shared.database.repository import AnalyticsRepository

logger = logging.getLogger(__name__)


@dataclass
class PipelineEvent:
    alert_type: str
    message: str
    visitor_id: Optional[uuid.UUID]
    payload: dict[str, Any]


class AlertEngine:
    """Generates VIP and repeat-visitor alerts from recognition outcomes."""

    def __init__(self, db: Session, settings: Settings, brand_id):
        self.repo = AnalyticsRepository(db, settings, brand_id)
        self.settings = settings
        self._redis = None
        if settings.redis_url:
            try:
                import redis

                self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            except Exception as exc:
                logger.warning("Redis unavailable: %s", exc)

    def process(
        self,
        match: MatchResult,
        *,
        track_id: int,
        confidence: float,
    ) -> list[PipelineEvent]:
        events: list[PipelineEvent] = []
        visitor = match.visitor
        meta = visitor.metadata_ or {}
        if meta.get("person_kind") == "employee":
            return events

        if visitor.is_vip:
            events.append(
                self._emit(
                    alert_type="vip_detected",
                    message=f"VIP visitor detected: {visitor.display_name}",
                    visitor=visitor,
                    payload={"track_id": track_id, "confidence": confidence},
                )
            )
        elif visitor.visit_count >= self.settings.vip_visit_threshold:
            visitor.is_vip = True
            events.append(
                self._emit(
                    alert_type="vip_detected",
                    message=f"Visitor promoted to VIP: {visitor.display_name}",
                    visitor=visitor,
                    payload={"track_id": track_id, "visit_count": visitor.visit_count},
                )
            )

        if not match.is_new and self.repo.was_repeat_within_window(visitor.id):
            events.append(
                self._emit(
                    alert_type="repeat_visitor",
                    message=f"Repeat visitor: {visitor.display_name}",
                    visitor=visitor,
                    payload={
                        "track_id": track_id,
                        "visit_count": visitor.visit_count,
                    },
                )
            )

        return events

    def _emit(
        self,
        *,
        alert_type: str,
        message: str,
        visitor: Visitor,
        payload: dict[str, Any],
    ) -> PipelineEvent:
        alert = self.repo.create_alert(
            store_id=self.settings.store_id,
            alert_type=alert_type,
            message=message,
            visitor_id=visitor.id,
            payload=payload,
        )
        self._publish(alert)
        return PipelineEvent(
            alert_type=alert_type,
            message=message,
            visitor_id=visitor.id,
            payload=payload,
        )

    def _publish(self, alert: Alert) -> None:
        if not self._redis:
            return
        channel = f"alerts:{alert.store_id}"
        payload = {
            "id": str(alert.id),
            "alert_type": alert.alert_type,
            "message": alert.message,
            "visitor_id": str(alert.visitor_id) if alert.visitor_id else None,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }
        try:
            self._redis.publish(channel, json.dumps(payload))
        except Exception as exc:
            logger.warning("Redis publish failed: %s", exc)
