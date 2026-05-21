from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend_core.schemas.admin import (
    BrandCreate,
    BrandOut,
    CameraCreate,
    CameraOut,
    EdgeDeviceCreate,
    EdgeDeviceOut,
    StoreCreate,
    StoreOut,
)
from edge_ai.camera_ingestion.rtsp_vendors import build_rtsp_url, validate_rtsp_url
from shared.database.tenant_models import Brand, Camera, EdgeDevice, Store
from shared.database.tenant_repository import TenantRepository
from shared.security import generate_api_key, hash_secret


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.tenants = TenantRepository(db)

    def create_brand(self, body: BrandCreate) -> BrandOut:
        if self.tenants.get_brand_by_slug(body.slug):
            raise HTTPException(status.HTTP_409_CONFLICT, "Brand slug exists")
        brand = Brand(slug=body.slug, name=body.name, settings=body.settings)
        self.db.add(brand)
        self.db.flush()
        return BrandOut(
            id=brand.id,
            slug=brand.slug,
            name=brand.name,
            is_active=brand.is_active,
            created_at=brand.created_at,
        )

    def create_store(self, body: StoreCreate) -> StoreOut:
        brand = self.tenants.get_brand_by_slug(body.brand_slug)
        if not brand:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Brand not found")
        if self.tenants.get_store(brand.id, body.external_id):
            raise HTTPException(status.HTTP_409_CONFLICT, "Store exists")
        store = Store(
            brand_id=brand.id,
            external_id=body.external_id,
            name=body.name,
            timezone=body.timezone,
        )
        self.db.add(store)
        self.db.flush()
        return StoreOut(
            id=store.id,
            brand_slug=brand.slug,
            external_id=store.external_id,
            name=store.name,
            config_version=store.config_version,
        )

    def create_camera(self, body: CameraCreate) -> CameraOut:
        brand = self.tenants.get_brand_by_slug(body.brand_slug)
        if not brand:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Brand not found")
        store = self.tenants.get_store(brand.id, body.store_id)
        if not store:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Store not found")

        if body.vendor and body.host:
            rtsp = build_rtsp_url(
                body.vendor,
                host=body.host,
                username=body.username,
                password=body.password,
                channel=body.channel,
            )
        elif body.rtsp_url:
            rtsp = body.rtsp_url
        else:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Provide rtsp_url or vendor+host credentials",
            )

        if not validate_rtsp_url(rtsp):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid RTSP URL")

        cam = Camera(
            store_id=store.id,
            external_id=body.external_id,
            name=body.name,
            rtsp_url=rtsp,
            frame_skip=body.frame_skip,
            metadata_={"vendor": body.vendor} if body.vendor else {},
        )
        self.db.add(cam)
        store.config_version += 1
        self.db.flush()
        return CameraOut(
            id=cam.id,
            external_id=cam.external_id,
            rtsp_url=cam.rtsp_url,
            name=cam.name,
            enabled=cam.enabled,
        )

    def create_edge_device(self, body: EdgeDeviceCreate) -> EdgeDeviceOut:
        brand = self.tenants.get_brand_by_slug(body.brand_slug)
        if not brand:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Brand not found")
        store = self.tenants.get_store(brand.id, body.store_id)
        if not store:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Store not found")
        key = generate_api_key("edge")
        device = EdgeDevice(
            store_id=store.id,
            name=body.name,
            api_key_hash=hash_secret(key),
            status="offline",
        )
        self.db.add(device)
        self.db.flush()
        return EdgeDeviceOut(
            id=device.id, name=device.name, api_key=key, status=device.status
        )
