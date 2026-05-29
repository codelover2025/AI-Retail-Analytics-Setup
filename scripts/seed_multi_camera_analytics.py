"""
Seed multi-camera analytics demo data (sessions, zones, interactions, daily footfall).

Usage:
  $env:PYTHONPATH="."
  python scripts/seed_multi_camera_analytics.py
"""
from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import get_settings
from shared.database.session import SessionLocal, init_db
from shared.database.tenant_models import Brand, Camera, Store
from backend_core.schemas.multi_camera import (
    AIAnalyticsIngestBatch,
    AISessionPayload,
    AIZonePayload,
    AIInteractionPayload,
)
from backend_core.services.multi_camera_analytics import MultiCameraAnalyticsService


ZONES = ["Entrance", "Showcase A", "Showcase B", "Billing", "Exit"]
CAMERA_NAMES = [
    ("cam-entrance", "Entrance"),
    ("cam-showcase-a", "Showcase A"),
    ("cam-showcase-b", "Showcase B"),
    ("cam-billing", "Billing"),
    ("cam-exit", "Exit"),
]


def seed() -> None:
    settings = get_settings()
    init_db()
    db = SessionLocal()
    try:
        brand = db.query(Brand).filter(Brand.slug == settings.brand_slug).one_or_none()
        if brand is None:
            print("Run scripts/seed_phase1.py first.")
            return
        store = (
            db.query(Store)
            .filter(Store.brand_id == brand.id, Store.external_id == settings.store_id)
            .one_or_none()
        )
        if store is None:
            print("Store missing — run seed_phase1.py")
            return

        for ext_id, name in CAMERA_NAMES:
            cam = (
                db.query(Camera)
                .filter(Camera.store_id == store.id, Camera.external_id == ext_id)
                .one_or_none()
            )
            if cam is None:
                db.add(
                    Camera(
                        store_id=store.id,
                        external_id=ext_id,
                        name=name,
                        rtsp_url=f"rtsp://demo/{ext_id}",
                        enabled=True,
                    )
                )
        db.commit()
        print(f"Ensured {len(CAMERA_NAMES)} cameras for store {store.external_id}")

        svc = MultiCameraAnalyticsService(
            db, settings, brand.id, store.external_id
        )
        now = datetime.now(timezone.utc)
        sessions: list[AISessionPayload] = []
        interactions: list[AIInteractionPayload] = []

        rng = random.Random(42)
        for day_offset in range(14):
            day_start = now - timedelta(days=day_offset)
            for cam_id, _ in CAMERA_NAMES:
                for i in range(rng.randint(8, 20)):
                    person = f"p-{cam_id}-{day_offset}-{i}"
                    dwell = round(rng.uniform(30, 600), 1)
                    entry = day_start.replace(
                        hour=rng.randint(9, 20),
                        minute=rng.randint(0, 59),
                        second=0,
                        microsecond=0,
                    )
                    zones = [
                        AIZonePayload(
                            zone_name=rng.choice(ZONES),
                            time_spent=round(dwell * rng.uniform(0.1, 0.5), 1),
                        )
                        for _ in range(rng.randint(1, 3))
                    ]
                    sessions.append(
                        AISessionPayload(
                            person_id=person,
                            camera_id=cam_id,
                            dwell_time=dwell,
                            zones=zones,
                            entry_time=entry,
                            exit_time=entry + timedelta(seconds=int(dwell)),
                        )
                    )
                    if rng.random() < 0.15:
                        interactions.append(
                            AIInteractionPayload(
                                customer_id=person,
                                employee_id=f"emp-{rng.randint(1, 5)}",
                                camera_id=cam_id,
                                timestamp=entry + timedelta(seconds=int(dwell * 0.5)),
                            )
                        )
                    if day_offset < 3 and rng.random() < 0.3:
                        sessions.append(
                            AISessionPayload(
                                person_id=person,
                                camera_id=cam_id,
                                dwell_time=round(dwell * 0.8, 1),
                                zones=zones[:1],
                                entry_time=entry + timedelta(days=1),
                            )
                        )

        batch = AIAnalyticsIngestBatch(
            store_id=store.external_id,
            sessions=sessions,
            interactions=interactions,
        )
        result = svc.ingest_batch(batch)
        db.commit()
        print(
            f"Ingested: {result.sessions_accepted} sessions, "
            f"{result.zone_logs_accepted} zone logs, "
            f"{result.interactions_accepted} interactions"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
