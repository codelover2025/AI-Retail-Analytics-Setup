from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend_core.schemas.contract import (
    AlertItem,
    FootfallDailyPoint,
    FootfallHourlyPoint,
    FootfallResponse,
    LiveVisitorsResponse,
    RecognitionItem,
    RecognitionType,
)
from shared.config import Settings
from shared.database.models import Alert, FootfallDaily, LiveVisitor, Recognition, Visitor
from shared.database.repository import AnalyticsRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _recognition_type(rec: Recognition, visitor: Visitor) -> RecognitionType:
    if visitor.is_vip:
        return "vip"
    if rec.is_new_visitor:
        return "new_visitor"
    if visitor.visit_count > 1:
        return "repeat_visitor"
    return "visitor"


class AnalyticsService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.repo = AnalyticsRepository(db, settings)

    def live_visitors(self, store_id: str | None) -> LiveVisitorsResponse:
        stmt = select(func.count(LiveVisitor.id), func.max(LiveVisitor.last_seen_at))
        if store_id:
            stmt = stmt.where(LiveVisitor.store_id == store_id)
        count, last_seen = self.db.execute(stmt).one()
        ts = last_seen or _utcnow()
        return LiveVisitorsResponse(count=int(count or 0), timestamp=ts)

    def recognitions(
        self,
        *,
        store_id: str | None,
        limit: int,
    ) -> list[RecognitionItem]:
        rows = self.repo.get_recognitions(store_id=store_id, limit=limit)
        out: list[RecognitionItem] = []
        for rec in rows:
            visitor = self.db.get(Visitor, rec.visitor_id)
            if not visitor:
                continue
            rtype = _recognition_type(rec, visitor)
            out.append(
                RecognitionItem(
                    id=str(rec.id),
                    type=rtype,
                    time=rec.recognized_at,
                )
            )
        return out

    def footfall(
        self,
        *,
        store_id: str | None,
        from_day: date | None,
        hourly_limit: int = 168,
    ) -> FootfallResponse:
        daily_rows = self.repo.get_footfall(store_id=store_id, from_day=from_day)
        daily = [
            FootfallDailyPoint(
                day=r.day,
                unique_visitors=r.unique_visitors,
                total_detections=r.total_detections,
            )
            for r in daily_rows
        ]

        bucket = func.date_trunc("hour", Recognition.recognized_at).label("bucket_start")
        stmt = (
            select(bucket, func.count().label("cnt"))
            .group_by(bucket)
            .order_by(bucket.desc())
            .limit(hourly_limit)
        )
        if store_id:
            stmt = stmt.where(Recognition.store_id == store_id)
        hourly_raw = self.db.execute(stmt).all()
        hourly = [
            FootfallHourlyPoint(bucket_start=row.bucket_start, count=int(row.cnt))
            for row in hourly_raw
        ]
        return FootfallResponse(daily=daily, hourly=hourly)

    def alerts(
        self,
        *,
        store_id: str | None,
        limit: int,
        unacknowledged_only: bool,
    ) -> list[AlertItem]:
        rows = self.repo.get_alerts(
            store_id=store_id,
            limit=limit,
            unacknowledged_only=unacknowledged_only,
        )
        return [
            AlertItem(type=a.alert_type, message=a.message, time=a.created_at)
            for a in rows
        ]
