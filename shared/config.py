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

    # Store / camera
    store_id: str = "store-001"
    camera_id: str = "cam-001"
    rtsp_url: str = "0"  # "0" = webcam, or rtsp://...

    # Recognition thresholds
    recognition_threshold: float = 0.45
    vip_visit_threshold: int = 10
    repeat_visit_window_hours: int = 24

    # Pipeline tuning
    frame_skip: int = 2
    det_size: int = 640
    max_live_visitor_seconds: int = 30

    # Auth (simple API key for dashboard)
    api_key: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
