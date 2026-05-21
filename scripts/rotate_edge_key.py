"""Rotate edge device API key and write EDGE_API_KEY to .env."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import get_settings
from shared.database.session import SessionLocal, init_db
from shared.database.tenant_models import EdgeDevice, Store
from shared.database.tenant_repository import TenantRepository
from shared.security import generate_api_key, hash_secret


def update_env_file(env_path: Path, key: str) -> None:
    line = f"EDGE_API_KEY={key}\n"
    if env_path.exists():
        text = env_path.read_text(encoding="utf-8")
        if re.search(r"^EDGE_API_KEY=", text, re.MULTILINE):
            text = re.sub(r"^EDGE_API_KEY=.*$", line.strip(), text, flags=re.MULTILINE)
        else:
            text = text.rstrip() + "\n" + line
        env_path.write_text(text, encoding="utf-8")
    else:
        env_path.write_text(line, encoding="utf-8")


def main() -> None:
    settings = get_settings()
    init_db()
    db = SessionLocal()
    edge_key = generate_api_key("edge")
    try:
        brand = TenantRepository(db).get_brand_by_slug(settings.brand_slug)
        if brand is None:
            raise SystemExit(f"Brand not found: {settings.brand_slug}. Run seed_phase1.py first.")
        store = TenantRepository(db).get_store(brand.id, settings.store_id)
        if store is None:
            raise SystemExit(f"Store not found: {settings.store_id}")
        device = (
            db.query(EdgeDevice)
            .filter(
                EdgeDevice.store_id == store.id,
                EdgeDevice.name == settings.edge_device_name,
            )
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
        else:
            device.api_key_hash = hash_secret(edge_key)
        db.commit()
        update_env_file(ROOT / ".env", edge_key)
        print(f"EDGE_API_KEY rotated and saved to .env")
        print(f"EDGE_API_KEY={edge_key}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
