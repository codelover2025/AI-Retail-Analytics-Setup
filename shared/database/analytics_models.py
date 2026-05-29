"""Multi-camera retail analytics tables (AI output → persistence only)."""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.models import Base


class AnalyticsSession(Base):
    __tablename__ = "analytics_sessions"
    __table_args__ = (
        Index("ix_analytics_sessions_brand_camera_entry", "brand_id", "camera_id", "entry_time"),
        Index("ix_analytics_sessions_brand_store_entry", "brand_id", "store_id", "entry_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    person_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    camera_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    store_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dwell_time: Mapped[float] = mapped_column(Float, default=0.0)


class ZoneLog(Base):
    __tablename__ = "zone_logs"
    __table_args__ = (
        Index("ix_zone_logs_brand_camera_zone", "brand_id", "camera_id", "zone_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    person_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    camera_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    store_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    zone_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    time_spent: Mapped[float] = mapped_column(Float, default=0.0)


class Interaction(Base):
    __tablename__ = "interactions"
    __table_args__ = (
        Index("ix_interactions_brand_camera_ts", "brand_id", "camera_id", "timestamp"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    employee_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    camera_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    store_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FootfallDailyCamera(Base):
    """Per-camera daily footfall (aggregated from sessions; no cross-camera identity merge)."""

    __tablename__ = "footfall_daily_camera"
    __table_args__ = (
        UniqueConstraint(
            "brand_id",
            "store_id",
            "camera_id",
            "day",
            name="uq_footfall_camera_brand_store_cam_day",
        ),
        Index("ix_footfall_daily_camera_brand_store_day", "brand_id", "store_id", "day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    day: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    store_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    camera_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    total_visitors: Mapped[int] = mapped_column(Integer, default=0)
    repeat_visitors: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
