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
    from datetime import time
    day_start = datetime.combine(day, time.min).replace(tzinfo=timezone.utc)
    day_end = datetime.combine(day, time.max).replace(tzinfo=timezone.utc)
    stmt = (
        select(
            AnalyticsSession.camera_id,
            AnalyticsSession.person_id,
            func.count().label("visits"),
        )
        .where(
            AnalyticsSession.brand_id == brand_id,
            AnalyticsSession.store_id == store_id,
            AnalyticsSession.entry_time >= day_start,
            AnalyticsSession.entry_time <= day_end,
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
        repeat = 0
        for person_id, visits in persons.items():
            # A person is a repeat visitor on this camera today if:
            # 1. They visited this camera in the past (prior to today) OR
            # 2. They visited this camera more than once today
            from datetime import time
            day_start = datetime.combine(day, time.min).replace(tzinfo=timezone.utc)
            prior_count = db.scalar(
                select(func.count())
                .select_from(AnalyticsSession)
                .where(
                    AnalyticsSession.brand_id == brand_id,
                    AnalyticsSession.store_id == store_id,
                    AnalyticsSession.camera_id == cam,
                    AnalyticsSession.person_id == person_id,
                    AnalyticsSession.entry_time < day_start,
                )
            ) or 0
            if prior_count > 0 or visits > 1:
                repeat += 1

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

    from datetime import time
    day_start = datetime.combine(day, time.min).replace(tzinfo=timezone.utc)
    day_end = datetime.combine(day, time.max).replace(tzinfo=timezone.utc)
    count_today = db.scalar(
        select(func.count())
        .select_from(AnalyticsSession)
        .where(
            AnalyticsSession.brand_id == brand_id,
            AnalyticsSession.person_id == person_id,
            AnalyticsSession.camera_id == camera_id,
            AnalyticsSession.store_id == store_id,
            AnalyticsSession.entry_time >= day_start,
            AnalyticsSession.entry_time <= day_end,
        )
    ) or 1

    if count_today == 1:
        # First session today: they represent a new unique visitor for this camera today.
        row.total_visitors += 1
        if prior_visits > 0:
            # They have visited this camera in the past: count as unique repeat today.
            row.repeat_visitors += 1
    elif count_today == 2 and prior_visits == 0:
        # Second session today, but no history from past days: they now cross the line
        # into being a repeat visitor for today.
        row.repeat_visitors += 1

    row.updated_at = _utcnow()
