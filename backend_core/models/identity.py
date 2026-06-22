"""PostgreSQL / SQLite tables for identity insights (no AI logic here)."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Uuid, func, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database.models import Base
from shared.database.types import JSONCol


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_brand_last_seen", "brand_id", "last_seen"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), index=True, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    visit_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Enrollment fields
    name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    membership_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    loyalty_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_store: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_watchlist: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    embeddings: Mapped[list["FaceEmbedding"]] = relationship(back_populates="customer")


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        Index("ix_employees_brand_active", "brand_id", "active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(JSONCol, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Enrollment fields
    email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    store_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    joining_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    employee_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class PersonRecognition(Base):
    """AI recognition log — exposed via GET /api/recognitions."""

    __tablename__ = "person_recognitions"
    __table_args__ = (
        Index("ix_person_recognitions_brand_store_timestamp", "brand_id", "store_id", "timestamp"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), index=True, nullable=True)
    store_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    person_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    camera_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    embedding: Mapped[list[float]] = mapped_column(JSONCol, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    customer: Mapped["Customer"] = relationship(back_populates="embeddings")
