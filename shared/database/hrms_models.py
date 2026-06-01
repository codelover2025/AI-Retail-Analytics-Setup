import uuid
from datetime import datetime
from sqlalchemy import DateTime, String, Uuid, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from shared.database.models import Base


class HRMSAttendanceSync(Base):
    __tablename__ = "hrms_attendance_syncs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="present", nullable=False)
