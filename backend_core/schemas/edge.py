from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CameraConfigOut(BaseModel):
    camera_id: str
    rtsp_url: str
    frame_skip: Optional[int] = None
    name: Optional[str] = None


class EdgeConfigResponse(BaseModel):
    config_version: int
    brand_slug: str
    store_id: str
    frame_skip: int
    det_size: int
    max_live_visitor_seconds: int
    recognition_threshold: float
    pipeline_backend: str
    cameras: list[CameraConfigOut]


class EdgeHeartbeatRequest(BaseModel):
    software_version: str = "1.0.0"
    pipeline_backend: str = "opencv"
    cameras_active: int = 0
    fps_avg: Optional[float] = None
    gpu_utilization: Optional[float] = None
    memory_mb: Optional[float] = None
    errors: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class EdgeHeartbeatResponse(BaseModel):
    status: str
    server_time: datetime
    config_version: int
    config_refresh: bool = False
