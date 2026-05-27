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

    # Recognition thresholds (cosine similarity; recommended 0.5–0.6)
    recognition_threshold: float = 0.55
    min_face_score: float = 0.6
    min_bbox_area: float = 1600.0  # min width*height (pixels²) for face bbox
    vip_visit_threshold: int = 10
    repeat_visit_window_hours: int = 24

    # Phase 2 — multi-frame match + FAISS gallery
    track_embed_min_frames: int = 3
    track_embed_max_frames: int = 8
    use_faiss: bool = True
    faiss_min_gallery_size: int = 50
    enrollment_min_frames: int = 3
    enrollment_frame_similarity: float = 0.6

    # Pipeline tuning
    frame_skip: int = 2
    det_size: int = 640
    max_live_visitor_seconds: int = 30
    insightface_ctx_id: int = -1  # -1 CPU, 0+ GPU (CUDA)
    edge_use_cloud_events: bool = False  # POST /api/v1/edge/events instead of direct DB

    # TLS / production (document in DEPLOY_INDIA.md)
    require_tls: bool = False

    # Auth
    api_key: Optional[str] = None
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24


@lru_cache
def get_settings() -> Settings:
    return Settings()
