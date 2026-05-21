"""Verify POST /api/v1/edge/events batch upload."""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import get_settings


def main() -> int:
    s = get_settings()
    if not s.edge_api_key:
        print("SKIP: EDGE_API_KEY not set")
        return 0
    payload = {
        "live_visitors": [
            {
                "camera_id": s.camera_id,
                "track_id": 9001,
                "bbox": [10, 10, 100, 100],
                "confidence": 0.9,
            }
        ],
        "alerts": [
            {
                "alert_type": "test_batch",
                "message": "Phase 1 edge events batch test",
            }
        ],
    }
    with httpx.Client(timeout=15.0) as client:
        r = client.post(
            "http://localhost:8000/api/v1/edge/events",
            headers={"X-Edge-Key": s.edge_api_key},
            json=payload,
        )
    if r.status_code == 200 and r.json().get("accepted", 0) >= 1:
        print(f"PASS: accepted={r.json()['accepted']}")
        return 0
    print(f"FAIL: {r.status_code} {r.text}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
