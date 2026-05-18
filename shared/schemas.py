import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class VisitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: Optional[str] = None
    is_vip: bool
    visit_count: int
    last_seen_at: datetime


class LiveVisitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    track_id: int
    visitor_id: Optional[uuid.UUID] = None
    store_id: str
    camera_id: str
    bbox: list[float]
    confidence: float
    last_seen_at: datetime
    visitor: Optional[VisitorOut] = None


class RecognitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    store_id: str
    camera_id: str
    visitor_id: uuid.UUID
    track_id: int
    confidence: float
    is_new_visitor: bool
    bbox: Optional[list[float]] = None
    recognized_at: datetime


class FootfallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    store_id: str
    day: date
    unique_visitors: int
    total_detections: int


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    store_id: str
    visitor_id: Optional[uuid.UUID] = None
    alert_type: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    acknowledged: bool
    created_at: datetime
