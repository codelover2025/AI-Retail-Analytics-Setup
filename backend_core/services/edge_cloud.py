from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend_core.schemas.edge import (
    CameraConfigOut,
    EdgeConfigResponse,
    EdgeHeartbeatRequest,
    EdgeHeartbeatResponse,
)
from shared.config import Settings
from shared.database.tenant_models import EdgeDevice
from shared.database.tenant_repository import TenantRepository


class EdgeCloudService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.tenants = TenantRepository(db)

    def build_config(self, device: EdgeDevice) -> EdgeConfigResponse:
        store = device.store
        brand = store.brand
        cameras = self.tenants.list_enabled_cameras(store.id)
        return EdgeConfigResponse(
            config_version=store.config_version,
            brand_slug=brand.slug,
            store_id=store.external_id,
            frame_skip=self.settings.frame_skip,
            det_size=self.settings.det_size,
            max_live_visitor_seconds=self.settings.max_live_visitor_seconds,
            recognition_threshold=self.settings.recognition_threshold,
            pipeline_backend=self.settings.pipeline_backend,
            cameras=[
                CameraConfigOut(
                    camera_id=c.external_id,
                    rtsp_url=c.rtsp_url,
                    frame_skip=c.frame_skip,
                    name=c.name,
                )
                for c in cameras
            ],
        )

    def record_heartbeat(
        self,
        device: EdgeDevice,
        body: EdgeHeartbeatRequest,
        *,
        known_config_version: int | None,
    ) -> EdgeHeartbeatResponse:
        now = datetime.now(timezone.utc)
        device.status = "online"
        device.software_version = body.software_version
        device.last_heartbeat_at = now
        device.last_metrics = {
            "pipeline_backend": body.pipeline_backend,
            "cameras_active": body.cameras_active,
            "fps_avg": body.fps_avg,
            "gpu_utilization": body.gpu_utilization,
            "memory_mb": body.memory_mb,
            "errors": body.errors,
            **body.extra,
        }
        self.db.flush()

        current_version = device.store.config_version
        refresh = (
            known_config_version is not None
            and known_config_version < current_version
        )
        return EdgeHeartbeatResponse(
            status="ok",
            server_time=now,
            config_version=current_version,
            config_refresh=refresh,
        )
