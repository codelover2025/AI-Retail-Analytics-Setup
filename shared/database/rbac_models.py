"""RBAC — User and permission models (Phase 4).

Roles form a hierarchy:
  super_admin > brand_admin > store_manager > staff_viewer
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.models import Base
from shared.database.types import JSONCol


class User(Base):
    """Platform user with a role scoped to brand (and optionally store)."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_brand_role", "brand_id", "role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=True
    )
    # brand_id=None → super_admin (cross-brand access)

    store_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # store_id=None → brand-wide; only used when role=store_manager or staff_viewer

    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)

    role: Mapped[str] = mapped_column(String(32), nullable=False)
    # super_admin | brand_admin | store_manager | staff_viewer

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    extra: Mapped[dict[str, Any]] = mapped_column(JSONCol, default=dict)
    # display_name, phone, etc.

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
