"""Multi-camera analytics API contracts."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class CameraListItem(BaseModel):
    camera_id: str
    name: Optional[str] = None
    enabled: bool = True


class FootfallCameraPoint(BaseModel):
    day: date
    camera_id: Optional[str] = None
    total_visitors: int
    repeat_visitors: int
    repeat_ratio: float = Field(description="repeat_visitors / total_visitors when total > 0")


class FootfallCameraResponse(BaseModel):
    store_id: str
    camera_id: Optional[str] = None
    aggregated: bool = False
    points: list[FootfallCameraPoint]
    summary: FootfallCameraPoint


class DwellTimeStats(BaseModel):
    camera_id: Optional[str] = None
    session_count: int
    avg_dwell_seconds: float
    min_dwell_seconds: float
    max_dwell_seconds: float
    p50_dwell_seconds: float


class ZoneAnalyticsItem(BaseModel):
    zone_name: str
    total_time_spent: float
    visit_count: int
    avg_time_spent: float


class ZoneAnalyticsResponse(BaseModel):
    camera_id: Optional[str] = None
    zones: list[ZoneAnalyticsItem]


class RepeatAnalyticsResponse(BaseModel):
    camera_id: Optional[str] = None
    total_visitors: int
    repeat_visitors: int
    new_visitors: int
    repeat_ratio: float


class InteractionItem(BaseModel):
    id: str
    customer_id: str
    employee_id: str
    camera_id: str
    timestamp: datetime


class InteractionsResponse(BaseModel):
    camera_id: Optional[str] = None
    total: int
    items: list[InteractionItem]


class AIZonePayload(BaseModel):
    zone_name: str
    time_spent: float


class AISessionPayload(BaseModel):
    person_id: str
    camera_id: str
    dwell_time: float
    zones: list[AIZonePayload] = Field(default_factory=list)
    journey_path: list[str] = Field(default_factory=list)
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    interaction: bool = False
    identity_type: str = "visitor"
    age_bucket: Optional[str] = None
    gender: Optional[str] = None


class AIInteractionPayload(BaseModel):
    customer_id: str
    employee_id: str
    camera_id: str
    timestamp: Optional[datetime] = None


class AIAnalyticsIngestBatch(BaseModel):
    """Raw AI batch — stored as-is per camera (no cross-camera identity merge)."""

    store_id: Optional[str] = None
    sessions: list[AISessionPayload] = Field(default_factory=list)
    interactions: list[AIInteractionPayload] = Field(default_factory=list)


class AIAnalyticsIngestResponse(BaseModel):
    sessions_accepted: int
    zone_logs_accepted: int
    interactions_accepted: int


class HeatmapCell(BaseModel):
    zone_name: str
    intensity: float = Field(ge=0.0, le=1.0)
    total_time_spent: float
    visit_count: int


class HeatmapResponse(BaseModel):
    camera_id: Optional[str] = None
    cells: list[HeatmapCell]


class JourneyStep(BaseModel):
    camera_id: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    dwell_time: float
    journey_path: list[str] = Field(default_factory=list)


class JourneyResponse(BaseModel):
    person_id: str
    cross_camera: bool
    steps: list[JourneyStep]


class SessionOut(BaseModel):
    id: str
    person_id: str
    camera_id: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    dwell_time: float
    journey_path: list[str] = Field(default_factory=list)
    identity_type: str = "visitor"


class DemographicsPoint(BaseModel):
    age_bucket: str
    gender: str
    count: int


class DemographicsResponse(BaseModel):
    store_id: str
    day: date
    points: list[DemographicsPoint]
