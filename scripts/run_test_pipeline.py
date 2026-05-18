"""
Example test pipeline — processes synthetic frames without a camera.

Usage:
  python scripts/run_test_pipeline.py
  python scripts/run_test_pipeline.py --frames 20
  python scripts/run_test_pipeline.py --webcam   # uses RTSP_URL=0 from .env
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from edge_ai.detection.mock_detector import MockFaceDetector
from edge_ai.pipeline import RetailAnalyticsPipeline
from shared.database.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("test_pipeline")


def _synthetic_frame(width: int = 640, height: int = 480) -> np.ndarray:
    frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    cv2.putText(
        frame,
        "TEST FRAME",
        (40, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (255, 255, 255),
        2,
    )
    return frame


def run_synthetic(frames: int) -> None:
    init_db()
    pipeline = RetailAnalyticsPipeline(source="0")
    pipeline.detector = MockFaceDetector(faces_per_frame=1)
    logger.info(
        "Running synthetic test (%d frames, mock detector — no InsightFace required)",
        frames,
    )

    for i in range(frames):
        frame = _synthetic_frame()
        pipeline._process_frame(frame)
        if (i + 1) % 5 == 0:
            logger.info("Processed %d / %d frames", i + 1, frames)

    logger.info("Synthetic test complete. Start API: uvicorn backend_core.main:app --reload")


def run_webcam(frames: int) -> None:
    pipeline = RetailAnalyticsPipeline(source="0")
    pipeline.run(max_frames=frames)


def main() -> None:
    parser = argparse.ArgumentParser(description="Retail analytics test pipeline")
    parser.add_argument("--frames", type=int, default=10, help="Number of frames to process")
    parser.add_argument(
        "--webcam",
        action="store_true",
        help="Use webcam/RTSP pipeline instead of synthetic frames",
    )
    args = parser.parse_args()

    if args.webcam:
        run_webcam(args.frames)
    else:
        run_synthetic(args.frames)


if __name__ == "__main__":
    main()
