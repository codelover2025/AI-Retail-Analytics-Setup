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
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    membership_id: str | None = None
    loyalty_points: int = 0
    is_vip: bool = False
    preferred_store: str | None = None
    notes: str | None = None
    is_watchlist: bool = False
    has_face_enrolled: bool = False


class CustomerCreateIn(BaseModel):
    """Create or update a customer profile."""

    id: str | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    visit_count: int | None = None
    embedding: list[float] | None = Field(
        default=None, description="Optional; stored as face embedding"
    )
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    membership_id: str | None = None
    loyalty_points: int | None = None
    is_vip: bool | None = None
    preferred_store: str | None = None
    notes: str | None = None
    is_watchlist: bool | None = None


class CustomerUpdateIn(BaseModel):
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    visit_count: int | None = None
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    membership_id: str | None = None
    loyalty_points: int | None = None
    is_vip: bool | None = None
    preferred_store: str | None = None
    notes: str | None = None
    is_watchlist: bool | None = None


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
    email: str | None = None
    phone: str | None = None
    department: str | None = None
    designation: str | None = None
    store_id: str | None = None
    branch: str | None = None
    joining_date: datetime | None = None
    employee_code: str | None = None
    has_face_enrolled: bool = False


class EmployeeCreateIn(BaseModel):
    """Create or update an employee profile."""

    id: str | None = None
    name: str
    embedding: list[float] | None = None
    email: str | None = None
    phone: str | None = None
    department: str | None = None
    designation: str | None = None
    store_id: str | None = None
    branch: str | None = None
    joining_date: datetime | None = None
    employee_code: str | None = None


class EmployeeUpdateIn(BaseModel):
    name: str | None = None
    active: bool | None = None
    email: str | None = None
    phone: str | None = None
    department: str | None = None
    designation: str | None = None
    store_id: str | None = None
    branch: str | None = None
    joining_date: datetime | None = None
    employee_code: str | None = None


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
