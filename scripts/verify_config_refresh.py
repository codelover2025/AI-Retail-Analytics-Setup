"""E2E: bump store config_version → heartbeat returns config_refresh=true."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import get_settings
from shared.database.session import SessionLocal, init_db
from shared.database.tenant_models import EdgeDevice, Store
from shared.database.tenant_repository import TenantRepository


def main() -> int:
    settings = get_settings()
    if not settings.edge_api_key:
        print("FAIL: EDGE_API_KEY not set — run: python scripts/rotate_edge_key.py")
        return 1

    init_db()
    db = SessionLocal()
    try:
        brand = TenantRepository(db).get_brand_by_slug(settings.brand_slug)
        store = TenantRepository(db).get_store(brand.id, settings.store_id)
        db.query(EdgeDevice).filter(
            EdgeDevice.store_id == store.id,
            EdgeDevice.name == settings.edge_device_name,
        ).one()
        old_version = store.config_version
        store.config_version = old_version + 1
        db.commit()
        print(f"Bumped config_version: {old_version} -> {store.config_version}")

        base = settings.backend_url.rstrip("/")
        url = f"{base}/api/v1/edge/heartbeat?config_version={old_version}"
        body = json.dumps(
            {
                "software_version": "verify-script",
                "pipeline_backend": "opencv",
                "cameras_active": 1,
            }
        ).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "X-Edge-Key": settings.edge_api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        if not data.get("config_refresh"):
            print(f"FAIL: expected config_refresh=true, got: {data}")
            return 1
        print("PASS: config_refresh=true when client version is stale")
        return 0
    except urllib.error.HTTPError as exc:
        print(f"FAIL: HTTP {exc.code} — is uvicorn running on port 8000?")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
