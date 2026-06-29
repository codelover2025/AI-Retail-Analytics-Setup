"""Unit tests for Camera Management (CRUD) in MultiCameraAnalyticsService."""

from __future__ import annotations

import uuid
from typing import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend_core.schemas.multi_camera import CameraCreateIn, CameraUpdateIn
from backend_core.services.multi_camera_analytics import MultiCameraAnalyticsService
from shared.config import Settings
from shared.database.models import Base
from shared.database.tenant_models import Brand, Store, Camera


@pytest.fixture(name="db")
def fixture_db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_camera_crud_operations(db: Session) -> None:
    # 1. Setup Brand and Store
    brand = Brand(slug="test-brand", name="Test Brand")
    db.add(brand)
    db.flush()

    store = Store(brand_id=brand.id, external_id="store-01", name="Store 01")
    db.add(store)
    db.flush()
    db.commit()

    settings = Settings(brand_slug="test-brand", store_id="store-01")
    svc = MultiCameraAnalyticsService(db, settings, brand.id, "store-01")

    # 2. Test List Cameras (should be empty initially)
    cameras = svc.list_cameras()
    assert len(cameras) == 0

    # 3. Test Create Camera
    create_payload = CameraCreateIn(
        external_id="cam-01",
        name="Entrance Camera",
        rtsp_url="rtsp://admin:admin@192.168.1.64:554/stream",
        enabled=True,
        frame_skip=5,
        store_id="store-01"
    )
    new_cam = svc.create_camera(create_payload)
    assert new_cam.external_id == "cam-01"
    assert new_cam.name == "Entrance Camera"
    assert new_cam.rtsp_url == "rtsp://admin:admin@192.168.1.64:554/stream"
    assert new_cam.enabled is True
    assert new_cam.frame_skip == 5
    assert new_cam.store_id == store.id

    # Verify store config version incremented
    db.refresh(store)
    assert store.config_version == 2

    # Verify it shows up in list
    cameras = svc.list_cameras()
    assert len(cameras) == 1
    assert cameras[0].camera_id == "cam-01"
    assert cameras[0].id == new_cam.id
    assert cameras[0].rtsp_url == "rtsp://admin:admin@192.168.1.64:554/stream"

    # 4. Test Update Camera
    update_payload = CameraUpdateIn(
        name="Entrance Camera Updated",
        rtsp_url="rtsp://admin:admin@192.168.1.100:554/live",
        enabled=False,
        frame_skip=10
    )
    updated_cam = svc.update_camera(new_cam.id, update_payload)
    assert updated_cam.name == "Entrance Camera Updated"
    assert updated_cam.rtsp_url == "rtsp://admin:admin@192.168.1.100:554/live"
    assert updated_cam.enabled is False
    assert updated_cam.frame_skip == 10

    # Verify store config version incremented again
    db.refresh(store)
    assert store.config_version == 3

    # 5. Test Delete Camera
    svc.delete_camera(new_cam.id)
    
    # Verify it is deleted
    cameras = svc.list_cameras()
    assert len(cameras) == 0

    # Verify store config version incremented again
    db.refresh(store)
    assert store.config_version == 4
