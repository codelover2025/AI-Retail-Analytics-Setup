import uuid
from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, String, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.models import Base


class DemographicsDaily(Base):
    __tablename__ = "demographics_daily"
    __table_args__ = (
        UniqueConstraint(
            "brand_id",
            "store_id",
            "day",
            "age_bucket",
            "gender",
            name="uq_demographics_daily_keys",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False
    )
    store_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    day: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    age_bucket: Mapped[str] = mapped_column(String(32), nullable=False)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
