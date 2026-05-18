import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Visitor(Base):
    __tablename__ = "visitors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(128))
    embedding: Mapped[list[float]] = mapped_column(JSONB, nullable=False)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSONB, default=dict
    )


class Recognition(Base):
    __tablename__ = "recognitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[str] = mapped_column(String(64), index=True)
    camera_id: Mapped[str] = mapped_column(String(64), index=True)
    visitor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    track_id: Mapped[int] = mapped_column(Integer, index=True)
    confidence: Mapped[float] = mapped_column(Float)
    is_new_visitor: Mapped[bool] = mapped_column(Boolean, default=False)
    bbox: Mapped[Optional[list[float]]] = mapped_column(JSONB)
    recognized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class LiveVisitor(Base):
    __tablename__ = "live_visitors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[str] = mapped_column(String(64), index=True)
    camera_id: Mapped[str] = mapped_column(String(64), index=True)
    track_id: Mapped[int] = mapped_column(Integer, index=True)
    visitor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), index=True
    )
    bbox: Mapped[list[float]] = mapped_column(JSONB)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FootfallDaily(Base):
    __tablename__ = "footfall_daily"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[str] = mapped_column(String(64), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    unique_visitors: Mapped[int] = mapped_column(Integer, default=0)
    total_detections: Mapped[int] = mapped_column(Integer, default=0)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[str] = mapped_column(String(64), index=True)
    visitor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    alert_type: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, default=dict)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
