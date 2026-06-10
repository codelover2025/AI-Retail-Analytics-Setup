"""Alert rule configuration model (Phase 4)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.models import Base
from shared.database.types import JSONCol


class AlertRule(Base):
    """Configurable alert thresholds per brand/store."""

    __tablename__ = "alert_rules"
    __table_args__ = (
        Index("ix_alert_rules_brand_store", "brand_id", "store_id"),
        Index("ix_alert_rules_type_enabled", "alert_type", "enabled"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    store_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    # store_id=None means brand-wide rule

    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    # vip_detected | watchlist_detected | camera_offline | low_traffic | high_crowd

    threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # semantic depends on alert_type:
    #   high_crowd  → max visitors count
    #   low_traffic → min visitors per hour
    #   camera_offline → offline seconds before alert

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    channels: Mapped[list] = mapped_column(JSONCol, default=list)
    # ["dashboard", "whatsapp", "email"]

    recipients: Mapped[list] = mapped_column(JSONCol, default=list)
    # phone numbers / email addresses to notify

    config: Mapped[dict[str, Any]] = mapped_column(JSONCol, default=dict)
    # extra rule-specific config (e.g. watchlist_person_ids, cooldown_minutes)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
