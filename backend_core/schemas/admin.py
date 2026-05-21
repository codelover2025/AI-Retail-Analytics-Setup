from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BrandCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=64)
    name: str
    settings: dict[str, Any] = Field(default_factory=dict)


class BrandOut(BaseModel):
    id: UUID
    slug: str
    name: str
    is_active: bool
    created_at: datetime


class StoreCreate(BaseModel):
    brand_slug: str
    external_id: str
    name: str
    timezone: str = "Asia/Kolkata"


class StoreOut(BaseModel):
    id: UUID
    brand_slug: str
    external_id: str
    name: str
    config_version: int


class CameraCreate(BaseModel):
    brand_slug: str
    store_id: str
    external_id: str
    rtsp_url: Optional[str] = None
    name: Optional[str] = None
    vendor: Optional[str] = None  # hikvision | dahua | cpplus
    host: Optional[str] = None  # NVR IP, e.g. 192.168.1.64
    username: str = "admin"
    password: str = "admin"
    channel: int = 102
    frame_skip: Optional[int] = None


class CameraOut(BaseModel):
    id: UUID
    external_id: str
    rtsp_url: str
    name: Optional[str]
    enabled: bool


class EdgeDeviceCreate(BaseModel):
    brand_slug: str
    store_id: str
    name: str


class EdgeDeviceOut(BaseModel):
    id: UUID
    name: str
    api_key: str
    status: str
