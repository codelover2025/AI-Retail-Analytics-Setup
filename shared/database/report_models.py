"""Report job and schedule persistence models (Phase 4)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import Boolean, DateTime, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.models import Base
from shared.database.types import JSONCol


class ReportJob(Base):
    """Tracks async report generation jobs."""

    __tablename__ = "report_jobs"
    __table_args__ = (
        Index("ix_report_jobs_brand_created", "brand_id", "created_at"),
        Index("ix_report_jobs_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    store_ids: Mapped[list] = mapped_column(JSONCol, default=list)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False)   # daily|weekly|monthly|custom
    output_format: Mapped[str] = mapped_column(String(16), nullable=False)  # pdf|excel|csv
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    # pending | running | completed | failed
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    params: Mapped[dict[str, Any]] = mapped_column(JSONCol, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)


class ReportSchedule(Base):
    """Recurring report delivery schedules."""

    __tablename__ = "report_schedules"
    __table_args__ = (
        Index("ix_report_schedules_brand_enabled", "brand_id", "enabled"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    store_ids: Mapped[list] = mapped_column(JSONCol, default=list)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False)
    output_format: Mapped[str] = mapped_column(String(16), nullable=False)
    cron_expr: Mapped[str] = mapped_column(String(64), nullable=False)   # e.g. "0 8 * * *"
    delivery_channels: Mapped[list] = mapped_column(JSONCol, default=list)  # ["email","whatsapp"]
    recipients: Mapped[list] = mapped_column(JSONCol, default=list)          # email / phone list
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
