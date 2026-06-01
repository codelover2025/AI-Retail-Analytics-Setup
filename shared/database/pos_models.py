import uuid
from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, String, Uuid, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from shared.database.models import Base


class POSPurchase(Base):
    __tablename__ = "pos_purchases"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    store_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    visitor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("visitors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    transaction_external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    items_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
