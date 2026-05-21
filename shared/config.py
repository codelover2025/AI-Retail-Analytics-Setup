from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = (
        "postgresql+psycopg2://retail:retail@localhost:5432/retail_analytics"
    )

    # Redis (optional pub/sub for live updates)
    redis_url: Optional[str] = None

    # Multi-tenant (Phase 1)
    brand_slug: str = "orzen-demo"
    store_id: str = "store-001"
    camera_id: str = "cam-001"
    brand_id: Optional[str] = None  # resolved UUID at runtime if empty

    # Edge ↔ cloud
    backend_url: str = "http://localhost:8000"
    edge_api_key: Optional[str] = None
    edge_device_name: str = "jetson-01"
    heartbeat_interval_seconds: int = 30
    pipeline_backend: str = "opencv"  # opencv | deepstream

    # Cameras: JSON list or single RTSP_URL fallback
    rtsp_url: str = "0"
    cameras_json: Optional[str] = None
    multi_camera_enabled: bool = False
    max_camera_workers: int = 4

    # Recognition thresholds
    recognition_threshold: float = 0.45
    vip_visit_threshold: int = 10
    repeat_visit_window_hours: int = 24

    # Pipeline tuning
    frame_skip: int = 2
    det_size: int = 640
    max_live_visitor_seconds: int = 30

    # Auth
    api_key: Optional[str] = None
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24


@lru_cache
def get_settings() -> Settings:
    return Settings()
