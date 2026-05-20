"""Cross-dialect column types (PostgreSQL prod, SQLite local dev)."""

import uuid

from sqlalchemy import JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column

PK_UUID = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
FK_UUID = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
FK_UUID_NULL = mapped_column(Uuid(as_uuid=True), index=True, nullable=True)
JSONCol = JSON
