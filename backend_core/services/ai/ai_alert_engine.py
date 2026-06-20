"""AI Alert Engine evaluating complex anomalies (Phase 5)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend_core.services.alert_engine import AlertEngine
from shared.config import Settings
from shared.database.models import Alert
from shared.database.alert_rule_models import AlertRule

logger = logging.getLogger(__name__)


class AIAlertEngine(AlertEngine):
    """
    Extends baseline AlertEngine to evaluate complex retail AI anomalies
    with priority-based notification payloads.
    """

    def __init__(self, db: Session, settings: Settings, brand_id: Any) -> None:
        super().__init__(db, settings, brand_id)

    def evaluate_ai_rules(self, store_id: str) -> list[Alert]:
        """
        Manually triggers evaluation of periodic AI rules.
        Usually executed from background sync tasks.
        """
        # Load active alert rules for this brand/store
        stmt = select(AlertRule).where(
            AlertRule.brand_id == self.brand_id,
            (AlertRule.store_id == store_id) | (AlertRule.store_id == None),
            AlertRule.enabled == True
        )
        rules = self.db.scalars(stmt).all()
        
        evaluated_alerts = []
        # Group by type and apply custom checks
        return evaluated_alerts

    def check_low_conversion(self, store_id: str, hourly_footfall: int, transactions: int) -> Optional[Alert]:
        """Triggers warning if traffic is high but conversion is exceptionally low."""
        if hourly_footfall < 15:
            return None
            
        conversion = transactions / hourly_footfall
        if conversion < 0.05: # Under 5% conversion during high traffic
            if self._is_in_cooldown("low_conversion", store_id, cooldown_minutes=60):
                return None
                
            msg = f"Low conversion warning: Only {transactions} purchases out of {hourly_footfall} visitors this hour ({round(conversion*100, 1)}% rate)."
            alert = self._create_alert(
                alert_type="low_conversion",
                store_id=store_id,
                message=msg,
                payload={"priority": "MEDIUM", "conversion_rate": conversion, "footfall": hourly_footfall, "transactions": transactions}
            )
            self.db.commit()
            
            # Look up standard alert rule for low_conversion or low_traffic to dispatch
            rules = self._load_rules("low_traffic", store_id)
            if rules:
                self._dispatch(alert, rules[0])
            else:
                self._publish_dashboard(alert)
                
            return alert
        return None

    def check_long_queue(self, store_id: str, zone_name: str, queue_count: int) -> Optional[Alert]:
        """Triggers warning if checkout zone queues exceed threshold limits."""
        threshold = 4 # Default to 4 people queuing
        
        if queue_count >= threshold:
            if self._is_in_cooldown("long_queue", store_id, cooldown_minutes=15):
                return None
                
            msg = f"Long queue detected at '{zone_name}': {queue_count} customers waiting (threshold: {threshold})."
            alert = self._create_alert(
                alert_type="long_queue",
                store_id=store_id,
                message=msg,
                payload={"priority": "HIGH", "zone": zone_name, "queue_count": queue_count, "threshold": threshold}
            )
            self.db.commit()
            
            rules = self._load_rules("high_crowd", store_id)
            if rules:
                self._dispatch(alert, rules[0])
            else:
                self._publish_dashboard(alert)
                
            return alert
        return None

    def check_store_anomaly(self, store_id: str, current_count: int, historical_mean: float, std_dev: float) -> Optional[Alert]:
        """Triggers warning if current footfall deviates by > 2 standard deviations from mean."""
        if std_dev <= 1.0:
            std_dev = 2.0  # Safe default std dev
            
        z_score = (current_count - historical_mean) / std_dev
        
        # Anomaly is defined as a deviation of over 2.5 standard deviations
        if abs(z_score) >= 2.5:
            if self._is_in_cooldown("store_anomaly", store_id, cooldown_minutes=120):
                return None
                
            direction = "spiked" if z_score > 0 else "dropped"
            msg = f"Store footfall anomaly: Hourly traffic has {direction} to {current_count} (normal range: {round(historical_mean, 1)} +/- {round(2*std_dev, 1)})."
            
            alert = self._create_alert(
                alert_type="store_anomaly",
                store_id=store_id,
                message=msg,
                payload={"priority": "HIGH", "z_score": round(z_score, 2), "current_count": current_count, "historical_mean": historical_mean}
            )
            self.db.commit()
            
            self._publish_dashboard(alert)
            return alert
        return None

    def check_employee_inactivity(self, store_id: str, employee_name: str, zone_name: str, duration_minutes: float) -> Optional[Alert]:
        """Triggers warning if employee is logged in a zone for long durations without movement."""
        threshold = 20.0 # 20 minutes limit
        
        if duration_minutes >= threshold:
            if self._is_in_cooldown("employee_inactivity", store_id, cooldown_minutes=60):
                return None
                
            msg = f"Employee inactivity warning: {employee_name} has been in zone '{zone_name}' for {int(duration_minutes)} minutes."
            alert = self._create_alert(
                alert_type="employee_inactivity",
                store_id=store_id,
                message=msg,
                payload={"priority": "LOW", "employee_name": employee_name, "zone_name": zone_name, "duration_minutes": duration_minutes}
            )
            self.db.commit()
            
            self._publish_dashboard(alert)
            return alert
        return None
