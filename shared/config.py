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

    # Phase 3 — multi-camera analytics engine
    max_cameras_per_worker: int = 3
    max_faces_per_frame: int = 5
    analytics_exit_timeout_seconds: float = 4.0
    analytics_batch_interval_seconds: float = 5.0
    analytics_queue_size: int = 32
    analytics_output_path: str = "./data/analytics_sessions.jsonl"
    zones_json: Optional[str] = None

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

    # Phase 4 — Dashboard / Aggregation
    dashboard_cache_ttl_seconds: int = 300
    max_store_comparison: int = 10

    # Phase 4 — WhatsApp Business
    whatsapp_provider: str = "meta"  # meta | stub
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    whatsapp_api_version: str = "v19.0"

    # Phase 4 — Email delivery
    email_provider: str = "smtp"  # smtp | sendgrid | ses
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_address: str = "noreply@example.com"
    sendgrid_api_key: Optional[str] = None

    # Phase 4 — HRMS Integration
    hrms_provider: Optional[str] = None  # generic | stub
    hrms_api_url: Optional[str] = None
    hrms_api_key: Optional[str] = None

    # Phase 4 — POS Integration
    pos_provider: Optional[str] = None  # generic | stub
    pos_api_url: Optional[str] = None
    pos_api_key: Optional[str] = None

    # Phase 4 — CRM Integration
    crm_provider: Optional[str] = None  # generic | stub
    crm_api_url: Optional[str] = None
    crm_api_key: Optional[str] = None

    # Phase 4 — Reporting
    reports_output_dir: str = "./data/reports"
    report_max_concurrent: int = 3

    # Phase 4 — Logging / Observability
    log_level: str = "INFO"
    log_format: str = "json"  # json | text
    app_env: str = "development"  # development | staging | production


@lru_cache
def get_settings() -> Settings:
    return Settings()
