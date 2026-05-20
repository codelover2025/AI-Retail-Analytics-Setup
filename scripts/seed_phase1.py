"""
Seed Phase 1 multi-tenant data: brand, store, cameras, edge device.

Usage:
  python scripts/seed_phase1.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import get_settings
from shared.database.session import SessionLocal, init_db
from shared.database.tenant_models import Brand, Camera, EdgeDevice, Store
from shared.security import generate_api_key, hash_secret


def seed() -> None:
    settings = get_settings()
    init_db()
    db = SessionLocal()
    edge_key = generate_api_key("edge")

    try:
        brand = db.query(Brand).filter(Brand.slug == settings.brand_slug).one_or_none()
        if brand is None:
            brand = Brand(
                slug=settings.brand_slug,
                name="Orzen Demo Jewellers",
                settings={"region": "IN", "data_residency": "IN"},
            )
            db.add(brand)
            db.flush()
            print(f"Created brand: {brand.slug} ({brand.id})")
        else:
            print(f"Brand exists: {brand.slug}")

        store = (
            db.query(Store)
            .filter(Store.brand_id == brand.id, Store.external_id == settings.store_id)
            .one_or_none()
        )
        if store is None:
            store = Store(
                brand_id=brand.id,
                external_id=settings.store_id,
                name="Flagship Store",
                timezone="Asia/Kolkata",
            )
            db.add(store)
            db.flush()
            print(f"Created store: {store.external_id}")
        else:
            print(f"Store exists: {store.external_id}")

        cam = (
            db.query(Camera)
            .filter(Camera.store_id == store.id, Camera.external_id == settings.camera_id)
            .one_or_none()
        )
        if cam is None:
            cam = Camera(
                store_id=store.id,
                external_id=settings.camera_id,
                name="Entrance",
                rtsp_url=settings.rtsp_url,
                enabled=True,
            )
            db.add(cam)
            print(f"Created camera: {cam.external_id} -> {cam.rtsp_url}")
        else:
            cam.rtsp_url = settings.rtsp_url
            print(f"Updated camera RTSP: {cam.external_id}")

        device = (
            db.query(EdgeDevice)
            .filter(EdgeDevice.store_id == store.id, EdgeDevice.name == settings.edge_device_name)
            .one_or_none()
        )
        if device is None:
            device = EdgeDevice(
                store_id=store.id,
                name=settings.edge_device_name,
                api_key_hash=hash_secret(edge_key),
                status="offline",
            )
            db.add(device)
            print(f"Created edge device: {device.name}")
            print(f"\n=== SAVE THIS EDGE API KEY ===\nEDGE_API_KEY={edge_key}\n")
        else:
            print(f"Edge device exists: {device.name} (key not rotated)")

        db.commit()
        print("\nSeed complete. Add EDGE_API_KEY to .env and restart edge-ai.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
