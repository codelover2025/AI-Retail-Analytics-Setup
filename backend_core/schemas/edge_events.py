from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EdgeLiveVisitorEvent(BaseModel):
    camera_id: str
    track_id: int
    visitor_id: Optional[UUID] = None
    bbox: list[float]
    confidence: float = 0.0


class EdgeRecognitionEvent(BaseModel):
    camera_id: str
    track_id: int
    visitor_id: UUID
    confidence: float
    is_new_visitor: bool = False
    bbox: Optional[list[float]] = None


class EdgeAlertEvent(BaseModel):
    alert_type: str
    message: str
    visitor_id: Optional[UUID] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class EdgeEventsBatch(BaseModel):
    live_visitors: list[EdgeLiveVisitorEvent] = Field(default_factory=list)
    recognitions: list[EdgeRecognitionEvent] = Field(default_factory=list)
    alerts: list[EdgeAlertEvent] = Field(default_factory=list)
    recorded_at: Optional[datetime] = None


class EdgeEventsBatchResponse(BaseModel):
    accepted: int
    status: str = "ok"
