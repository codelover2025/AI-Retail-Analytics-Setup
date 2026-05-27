"""Strict API response shapes for identity endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RecognitionType = Literal[
    "customer",
    "employee",
    "new_visitor",
    "repeat_visitor",
    "visitor",
    "vip",
]


class CustomerOut(BaseModel):
    id: str
    first_seen: datetime
    last_seen: datetime
    visit_count: int


class CustomerCreateIn(BaseModel):
    """Create or update a customer profile.

    Notes:
    - This layer does NOT generate embeddings; it only stores provided embeddings.
    """

    id: str | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    visit_count: int | None = None
    embedding: list[float] | None = Field(
        default=None, description="Optional; stored as face embedding"
    )


class CustomerUpdateIn(BaseModel):
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    visit_count: int | None = None


class CustomerEnrollIn(BaseModel):
    embedding: list[float]


class RecognitionOut(BaseModel):
    id: str
    person_id: str
    type: str
    timestamp: datetime
    camera_id: str


class RepeatVisitorOut(BaseModel):
    person_id: str
    visit_count: int
    first_seen: datetime
    last_seen: datetime


class EmployeeOut(BaseModel):
    id: str
    name: str
    active: bool = True
    created_at: datetime
    updated_at: datetime | None = None


class EmployeeCreateIn(BaseModel):
    """Create or update an employee profile (JSON embedding)."""

    id: str | None = None
    name: str
    embedding: list[float]


class EmployeeUpdateIn(BaseModel):
    name: str | None = None
    active: bool | None = None


class RecognitionIngest(BaseModel):
    """Payload from AI pipeline — consumed as-is."""

    person_id: str
    type: str
    timestamp: datetime
    camera_id: str
    embedding: list[float] | None = Field(
        default=None, description="Optional; stored when type is customer"
    )


class IdentityStatsOut(BaseModel):
    total_customers: int
    repeat_visitors: int
    new_visitors_today: int
    employee_tags: int
