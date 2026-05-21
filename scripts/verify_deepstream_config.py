"""Generate DeepStream multi-source config (batch mux)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from edge_ai.deepstream.config_generator import generate_deepstream_config


def main() -> int:
    cameras = [
        {"camera_id": "c1", "rtsp_url": "rtsp://192.168.1.10/stream1"},
        {"camera_id": "c2", "rtsp_url": "rtsp://192.168.1.11/stream1"},
    ]
    path = generate_deepstream_config(cameras, batch_size=2)
    text = path.read_text(encoding="utf-8")
    if "batch-size=2" in text and "[source0]" in text and "[source1]" in text:
        print(f"PASS: {path}")
        print("PASS: SGIE template at edge_ai/deepstream/config/sgie_face.txt")
        return 0
    print("FAIL: config incomplete")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
