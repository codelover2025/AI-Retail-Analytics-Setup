"""Roll up per-camera session data into daily footfall summaries."""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.database.analytics_models import AnalyticsSession, FootfallDailyCamera
from shared.database.multi_camera_repository import MultiCameraAnalyticsRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def refresh_footfall_for_day(
    db: Session,
    brand_id: uuid.UUID,
    store_id: str,
    day: date,
    *,
    camera_id: str | None = None,
) -> int:
    """Recompute footfall_daily_camera from analytics_sessions for one day."""
    repo = MultiCameraAnalyticsRepository(db, brand_id)
    stmt = (
        select(
            AnalyticsSession.camera_id,
            AnalyticsSession.person_id,
            func.count().label("visits"),
        )
        .where(
            AnalyticsSession.brand_id == brand_id,
            AnalyticsSession.store_id == store_id,
            func.date(AnalyticsSession.entry_time) == day,
        )
        .group_by(AnalyticsSession.camera_id, AnalyticsSession.person_id)
    )
    if camera_id:
        stmt = stmt.where(AnalyticsSession.camera_id == camera_id)

    rows = db.execute(stmt).all()
    by_camera: dict[str, dict[str, int]] = {}
    for row in rows:
        cam = row.camera_id
        by_camera.setdefault(cam, {})[row.person_id] = int(row.visits)

    updated = 0
    for cam, persons in by_camera.items():
        total = len(persons)
        repeat = sum(1 for v in persons.values() if v > 1)
        footfall = repo.get_or_create_footfall_row(store_id=store_id, camera_id=cam, day=day)
        footfall.total_visitors = total
        footfall.repeat_visitors = repeat
        footfall.updated_at = _utcnow()
        updated += 1
    return updated


def upsert_footfall_on_session(
    db: Session,
    brand_id: uuid.UUID,
    *,
    store_id: str,
    camera_id: str,
    person_id: str,
    entry_time: datetime,
    prior_visits: int,
) -> None:
    """Increment daily footfall when a new session is ingested."""
    day = entry_time.date()
    repo = MultiCameraAnalyticsRepository(db, brand_id)
    row = repo.get_or_create_footfall_row(store_id=store_id, camera_id=camera_id, day=day)
    row.total_visitors += 1
    if prior_visits > 0:
        row.repeat_visitors += 1
    row.updated_at = _utcnow()
