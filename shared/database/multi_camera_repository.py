"""Persistence for multi-camera analytics (ingest + queries)."""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.database.analytics_models import (
    AnalyticsSession,
    FootfallDailyCamera,
    Interaction,
    ZoneLog,
)


class MultiCameraAnalyticsRepository:
    def __init__(self, db: Session, brand_id: uuid.UUID):
        self.db = db
        self.brand_id = brand_id

    def add_session(
        self,
        *,
        person_id: str,
        camera_id: str,
        store_id: str,
        entry_time: datetime,
        exit_time: Optional[datetime],
        dwell_time: float,
        journey_path: Optional[list[str]] = None,
    ) -> AnalyticsSession:
        row = AnalyticsSession(
            brand_id=self.brand_id,
            person_id=person_id,
            camera_id=camera_id,
            store_id=store_id,
            entry_time=entry_time,
            exit_time=exit_time,
            dwell_time=dwell_time,
            journey_path=journey_path or [],
        )
        self.db.add(row)
        return row

    def add_zone_log(
        self,
        *,
        person_id: str,
        camera_id: str,
        store_id: str,
        zone_name: str,
        time_spent: float,
    ) -> ZoneLog:
        row = ZoneLog(
            brand_id=self.brand_id,
            person_id=person_id,
            camera_id=camera_id,
            store_id=store_id,
            zone_name=zone_name,
            time_spent=time_spent,
        )
        self.db.add(row)
        return row

    def add_interaction(
        self,
        *,
        customer_id: str,
        employee_id: str,
        camera_id: str,
        store_id: str,
        timestamp: datetime,
    ) -> Interaction:
        row = Interaction(
            brand_id=self.brand_id,
            customer_id=customer_id,
            employee_id=employee_id,
            camera_id=camera_id,
            store_id=store_id,
            timestamp=timestamp,
        )
        self.db.add(row)
        return row

    def get_or_create_footfall_row(
        self, *, store_id: str, camera_id: str, day: date
    ) -> FootfallDailyCamera:
        row = self.db.scalar(
            select(FootfallDailyCamera).where(
                FootfallDailyCamera.brand_id == self.brand_id,
                FootfallDailyCamera.store_id == store_id,
                FootfallDailyCamera.camera_id == camera_id,
                FootfallDailyCamera.day == day,
            )
        )
        if row is not None:
            return row
        row = FootfallDailyCamera(
            brand_id=self.brand_id,
            store_id=store_id,
            camera_id=camera_id,
            day=day,
            total_visitors=0,
            repeat_visitors=0,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def count_sessions_for_person_camera(
        self, *, person_id: str, camera_id: str, store_id: str, before: datetime
    ) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(AnalyticsSession)
                .where(
                    AnalyticsSession.brand_id == self.brand_id,
                    AnalyticsSession.person_id == person_id,
                    AnalyticsSession.camera_id == camera_id,
                    AnalyticsSession.store_id == store_id,
                    AnalyticsSession.entry_time < before,
                )
            )
            or 0
        )
