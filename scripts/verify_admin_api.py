"""Verify admin provisioning API."""
from __future__ import annotations

import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import get_settings


def main() -> int:
    s = get_settings()
    if not s.api_key:
        print("SKIP: API_KEY not set")
        return 0
    base = "http://localhost:8000"
    headers = {"X-API-Key": s.api_key}
    slug = "phase1-test-brand"

    with httpx.Client(timeout=15.0) as client:
        r = client.post(
            f"{base}/api/v1/admin/brands",
            headers=headers,
            json={"slug": slug, "name": "Phase1 Test Brand"},
        )
        if r.status_code == 409:
            print("Brand exists (OK)")
        elif r.status_code == 200:
            print(f"PASS: created brand {r.json()['slug']}")
        else:
            print(f"FAIL: brand {r.status_code} {r.text}")
            return 1

        r2 = client.post(
            f"{base}/api/v1/admin/cameras",
            headers=headers,
            json={
                "brand_slug": s.brand_slug,
                "store_id": s.store_id,
                "external_id": "cam-hik-test",
                "vendor": "hikvision",
                "host": "192.168.1.64",
                "username": "admin",
                "password": "secret",
                "channel": 102,
                "name": "Entrance Hikvision",
            },
        )
        if r2.status_code in (200, 409):
            url = r2.json().get("rtsp_url", "")
            if "Streaming/Channels" in url or r2.status_code == 409:
                print(f"PASS: Hikvision RTSP builder — {url[:60]}...")
                return 0
        print(f"FAIL: camera {r2.status_code} {r2.text}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
