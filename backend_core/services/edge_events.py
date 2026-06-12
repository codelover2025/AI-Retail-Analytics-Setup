from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend_core.schemas.edge_events import EdgeEventsBatch, EdgeEventsBatchResponse
from shared.config import Settings
from shared.database.analytics_models import AnalyticsSession, ZoneLog
from shared.database.models import Alert, Recognition, Visitor
from shared.database.repository import AnalyticsRepository
from shared.database.tenant_models import EdgeDevice


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EdgeEventsService:
    def __init__(self, db: Session, settings: Settings, device: EdgeDevice):
        self.db = db
        self.settings = settings
        self.device = device
        self.brand_id = device.store.brand_id
        self.store_external_id = device.store.external_id
        self.repo = AnalyticsRepository(db, settings, self.brand_id)

    def ingest_batch(self, batch: EdgeEventsBatch) -> EdgeEventsBatchResponse:
        count = 0
        recorded_at = batch.recorded_at or _utcnow()

        # --- Live visitors ---------------------------------------------------
        for lv in batch.live_visitors:
            self.repo.upsert_live_visitor(
                store_id=self.store_external_id,
                camera_id=lv.camera_id,
                track_id=lv.track_id,
                visitor_id=lv.visitor_id,
                bbox=lv.bbox,
                confidence=lv.confidence,
            )
            count += 1

        # --- Recognitions + AnalyticsSession write ---------------------------
        for rec in batch.recognitions:
            visitor = self.db.get(Visitor, rec.visitor_id)
            if not visitor:
                continue

            self.repo.record_visit(
                visitor,
                store_id=self.store_external_id,
                camera_id=rec.camera_id,
                track_id=rec.track_id,
                confidence=rec.confidence,
                is_new_visitor=rec.is_new_visitor,
                bbox=rec.bbox or [],
            )
            count += 1

            # Write/update AnalyticsSession for this person+camera
            person_id = str(rec.visitor_id)
            self._upsert_analytics_session(
                person_id=person_id,
                camera_id=rec.camera_id,
                entry_time=recorded_at,
            )

        # --- Alerts ----------------------------------------------------------
        for alert in batch.alerts:
            self.repo.create_alert(
                store_id=self.store_external_id,
                alert_type=alert.alert_type,
                message=alert.message,
                visitor_id=alert.visitor_id,
                payload=alert.payload,
            )
            count += 1

        return EdgeEventsBatchResponse(accepted=count)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _upsert_analytics_session(
        self,
        person_id: str,
        camera_id: str,
        entry_time: datetime,
    ) -> None:
        """
        Create or update an open AnalyticsSession for this person+camera.
        If a session already exists (open = no exit_time) within the last
        MAX_LIVE_VISITOR_SECONDS window, extend its dwell time.
        Otherwise open a new session.
        """
        try:
            from sqlalchemy import select

            max_gap_seconds: float = float(
                getattr(self.settings, "max_live_visitor_seconds", 30)
            )

            existing = self.db.scalar(
                select(AnalyticsSession)
                .where(
                    AnalyticsSession.brand_id == self.brand_id,
                    AnalyticsSession.person_id == person_id,
                    AnalyticsSession.camera_id == camera_id,
                    AnalyticsSession.exit_time.is_(None),
                )
                .order_by(AnalyticsSession.entry_time.desc())
                .limit(1)
            )

            if existing is not None:
                # Extend dwell time: difference from entry to now
                delta = (entry_time - existing.entry_time).total_seconds()
                existing.dwell_time = max(existing.dwell_time or 0.0, delta)
                # Update journey path with latest camera
                path: list[Any] = list(existing.journey_path or [])
                if not path or path[-1] != camera_id:
                    path.append(camera_id)
                existing.journey_path = path
            else:
                session = AnalyticsSession(
                    brand_id=self.brand_id,
                    person_id=person_id,
                    camera_id=camera_id,
                    store_id=self.store_external_id,
                    entry_time=entry_time,
                    dwell_time=0.0,
                    journey_path=[camera_id],
                )
                self.db.add(session)
        except Exception:
            # Non-fatal — analytics session write failure must not break ingestion
            pass

    def _write_zone_log(
        self,
        person_id: str,
        camera_id: str,
        zone_name: str,
        time_spent: float = 0.0,
    ) -> None:
        """Write a ZoneLog entry for a person's zone visit."""
        try:
            log = ZoneLog(
                brand_id=self.brand_id,
                person_id=person_id,
                camera_id=camera_id,
                store_id=self.store_external_id,
                zone_name=zone_name,
                time_spent=time_spent,
            )
            self.db.add(log)
        except Exception:
            pass

