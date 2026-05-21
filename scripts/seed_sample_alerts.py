"""Insert sample alerts so GET /api/alerts returns data for dashboard demos."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import get_settings
from shared.database.models import Alert
from shared.database.session import SessionLocal, init_db
from shared.database.tenant_repository import TenantRepository


def seed() -> None:
    settings = get_settings()
    init_db()
    db = SessionLocal()
    try:
        brand = TenantRepository(db).get_brand_by_slug(settings.brand_slug)
        if brand is None:
            raise SystemExit("Run scripts/seed_phase1.py first")
        store_id = settings.store_id
        existing = (
            db.query(Alert)
            .filter(Alert.brand_id == brand.id, Alert.store_id == store_id)
            .count()
        )
        if existing >= 2:
            print(f"Alerts already present ({existing}); skip seed")
            return

        samples = [
            ("vip_detected", "VIP visitor detected at entrance (demo)"),
            ("repeat_visitor", "Repeat visitor returned within 24h (demo)"),
            ("system", "Phase 1 handoff test alert"),
        ]
        now = datetime.now(timezone.utc)
        for alert_type, message in samples:
            db.add(
                Alert(
                    brand_id=brand.id,
                    store_id=store_id,
                    alert_type=alert_type,
                    message=message,
                    payload={"source": "seed_sample_alerts"},
                    created_at=now,
                )
            )
        db.commit()
        print(f"Created {len(samples)} sample alerts for store {store_id}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
