import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import numpy as np
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from shared.config import Settings
from shared.database.models import Alert, FootfallDaily, LiveVisitor, Recognition, Visitor


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AnalyticsRepository:
    """Persistence layer shared by edge pipeline and API."""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def list_visitors_with_embeddings(self) -> list[Visitor]:
        return list(self.db.scalars(select(Visitor)).all())

    def find_best_match(
        self, embedding: np.ndarray, threshold: Optional[float] = None
    ) -> tuple[Optional[Visitor], float]:
        threshold = threshold or self.settings.recognition_threshold
        visitors = self.list_visitors_with_embeddings()
        if not visitors:
            return None, 0.0

        best_visitor: Optional[Visitor] = None
        best_score = -1.0

        for visitor in visitors:
            stored = np.array(visitor.embedding, dtype=np.float32)
            score = float(np.dot(embedding, stored) / (
                np.linalg.norm(embedding) * np.linalg.norm(stored) + 1e-8
            ))
            if score > best_score:
                best_score = score
                best_visitor = visitor

        if best_visitor is None or best_score < threshold:
            return None, best_score
        return best_visitor, best_score

    def register_visitor(
        self,
        embedding: list[float],
        display_name: Optional[str] = None,
        is_vip: bool = False,
    ) -> Visitor:
        visitor = Visitor(
            embedding=embedding,
            display_name=display_name,
            is_vip=is_vip,
            visit_count=0,
            first_seen_at=_utcnow(),
            last_seen_at=_utcnow(),
        )
        self.db.add(visitor)
        self.db.flush()
        return visitor

    def record_visit(
        self,
        visitor: Visitor,
        *,
        store_id: str,
        camera_id: str,
        track_id: int,
        confidence: float,
        is_new_visitor: bool,
        bbox: list[float],
    ) -> Recognition:
        visitor.visit_count += 1
        visitor.last_seen_at = _utcnow()
        recognition = Recognition(
            store_id=store_id,
            camera_id=camera_id,
            visitor_id=visitor.id,
            track_id=track_id,
            confidence=confidence,
            is_new_visitor=is_new_visitor,
            bbox=bbox,
            recognized_at=_utcnow(),
        )
        self.db.add(recognition)
        self._increment_footfall(store_id)
        return recognition

    def _increment_footfall(self, store_id: str) -> None:
        today = _utcnow().date()
        row = self.db.scalar(
            select(FootfallDaily).where(
                FootfallDaily.store_id == store_id,
                FootfallDaily.day == today,
            )
        )
        if row is None:
            row = FootfallDaily(
                store_id=store_id,
                day=today,
                unique_visitors=0,
                total_detections=0,
            )
            self.db.add(row)
        row.total_detections += 1

    def increment_unique_footfall(self, store_id: str) -> None:
        today = _utcnow().date()
        row = self.db.scalar(
            select(FootfallDaily).where(
                FootfallDaily.store_id == store_id,
                FootfallDaily.day == today,
            )
        )
        if row is None:
            row = FootfallDaily(
                store_id=store_id,
                day=today,
                unique_visitors=1,
                total_detections=0,
            )
            self.db.add(row)
        else:
            row.unique_visitors += 1

    def upsert_live_visitor(
        self,
        *,
        store_id: str,
        camera_id: str,
        track_id: int,
        visitor_id: Optional[uuid.UUID],
        bbox: list[float],
        confidence: float,
    ) -> LiveVisitor:
        existing = self.db.scalar(
            select(LiveVisitor).where(
                LiveVisitor.store_id == store_id,
                LiveVisitor.camera_id == camera_id,
                LiveVisitor.track_id == track_id,
            )
        )
        now = _utcnow()
        if existing:
            existing.visitor_id = visitor_id
            existing.bbox = bbox
            existing.confidence = confidence
            existing.last_seen_at = now
            return existing

        live = LiveVisitor(
            store_id=store_id,
            camera_id=camera_id,
            track_id=track_id,
            visitor_id=visitor_id,
            bbox=bbox,
            confidence=confidence,
            last_seen_at=now,
        )
        self.db.add(live)
        return live

    def prune_stale_live_visitors(self, store_id: str, max_age_seconds: int) -> int:
        cutoff = _utcnow() - timedelta(seconds=max_age_seconds)
        result = self.db.execute(
            delete(LiveVisitor).where(
                LiveVisitor.store_id == store_id,
                LiveVisitor.last_seen_at < cutoff,
            )
        )
        return result.rowcount or 0

    def create_alert(
        self,
        *,
        store_id: str,
        alert_type: str,
        message: str,
        visitor_id: Optional[uuid.UUID] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> Alert:
        alert = Alert(
            store_id=store_id,
            visitor_id=visitor_id,
            alert_type=alert_type,
            message=message,
            payload=payload or {},
        )
        self.db.add(alert)
        return alert

    def was_repeat_within_window(self, visitor_id: uuid.UUID) -> bool:
        window = timedelta(hours=self.settings.repeat_visit_window_hours)
        cutoff = _utcnow() - window
        count = self.db.scalar(
            select(func.count())
            .select_from(Recognition)
            .where(
                Recognition.visitor_id == visitor_id,
                Recognition.recognized_at >= cutoff,
            )
        )
        return (count or 0) > 1

    def get_live_visitors(self, store_id: Optional[str] = None) -> list[LiveVisitor]:
        stmt = select(LiveVisitor).order_by(LiveVisitor.last_seen_at.desc())
        if store_id:
            stmt = stmt.where(LiveVisitor.store_id == store_id)
        return list(self.db.scalars(stmt).all())

    def get_recognitions(
        self,
        store_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Recognition]:
        stmt = select(Recognition).order_by(Recognition.recognized_at.desc()).limit(limit)
        if store_id:
            stmt = stmt.where(Recognition.store_id == store_id)
        return list(self.db.scalars(stmt).all())

    def get_footfall(
        self,
        store_id: Optional[str] = None,
        from_day: Optional[date] = None,
    ) -> list[FootfallDaily]:
        stmt = select(FootfallDaily).order_by(FootfallDaily.day.desc())
        if store_id:
            stmt = stmt.where(FootfallDaily.store_id == store_id)
        if from_day:
            stmt = stmt.where(FootfallDaily.day >= from_day)
        return list(self.db.scalars(stmt).all())

    def get_alerts(
        self,
        store_id: Optional[str] = None,
        limit: int = 50,
        unacknowledged_only: bool = False,
    ) -> list[Alert]:
        stmt = select(Alert).order_by(Alert.created_at.desc()).limit(limit)
        if store_id:
            stmt = stmt.where(Alert.store_id == store_id)
        if unacknowledged_only:
            stmt = stmt.where(Alert.acknowledged.is_(False))
        return list(self.db.scalars(stmt).all())
