"""Verify multi-camera config loads (no webcam required)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from edge_ai.camera_ingestion.camera_config import load_camera_sources
from shared.config import Settings


def main() -> int:
    cameras_json = os.environ.get(
        "CAMERAS_JSON",
        json.dumps(
            [
                {"camera_id": "cam-001", "rtsp_url": "0"},
                {"camera_id": "cam-002", "rtsp_url": "0"},
            ]
        ),
    )
    settings = Settings(
        cameras_json=cameras_json,
        multi_camera_enabled=True,
        brand_slug="orzen-demo",
        store_id="store-001",
        camera_id="cam-001",
    )
    sources = load_camera_sources(settings)
    if len(sources) < 2:
        print(f"FAIL: expected 2 cameras, got {len(sources)}")
        return 1
    ids = [s.camera_id for s in sources]
    print(f"PASS: loaded {len(sources)} cameras: {ids}")
    print("Manual: set MULTI_CAMERA_ENABLED=true and CAMERAS_JSON in .env, then: python -m edge_ai")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
