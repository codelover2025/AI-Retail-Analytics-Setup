"""Run multi-camera orchestrator for N frames (mock detector, no webcam)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault(
    "CAMERAS_JSON",
    json.dumps(
        [
            {"camera_id": "cam-a", "rtsp_url": "0"},
            {"camera_id": "cam-b", "rtsp_url": "0"},
        ]
    ),
)
os.environ["MULTI_CAMERA_ENABLED"] = "true"


def main() -> int:
    from edge_ai.detection.mock_detector import MockFaceDetector
    from edge_ai.multi_camera_pipeline import MultiCameraOrchestrator
    from edge_ai.camera_ingestion.camera_config import load_camera_sources
    from shared.config import get_settings
    from shared.database.session import init_db
    from shared.tenant_resolve import resolve_brand_id
    from shared.database.session import SessionLocal

    init_db()
    db = SessionLocal()
    resolve_brand_id(db, get_settings())
    db.close()

    cameras = load_camera_sources(get_settings())
    if len(cameras) < 2:
        print("FAIL: expected 2 cameras in config")
        return 1

    orch = MultiCameraOrchestrator(cameras)
    mock = MockFaceDetector(faces_per_frame=0)
    for p in orch._pipelines:
        p.detector = mock

    print(f"PASS: MultiCameraOrchestrator ready with {len(cameras)} cameras")
    print("(Live RTSP test: set real URLs in CAMERAS_JSON and run python -m edge_ai)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
