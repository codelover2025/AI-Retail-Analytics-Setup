from sqlalchemy.orm import Session

from backend_core.schemas.edge_events import EdgeEventsBatch, EdgeEventsBatchResponse
from shared.config import Settings
from shared.database.models import Alert, Recognition, Visitor
from shared.database.repository import AnalyticsRepository
from shared.database.tenant_models import EdgeDevice


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
