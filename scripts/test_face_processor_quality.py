"""BBox area + confidence gates."""

import numpy as np

from edge_ai.detection.face_detector import DetectedFace
from edge_ai.pipeline.face_processor import FaceProcessor


def main() -> None:
    proc = FaceProcessor(min_confidence=0.6, min_bbox_area=1600)
    small = DetectedFace(
        bbox=np.array([0, 0, 30, 30], dtype=np.float32),
        score=0.9,
        embedding=np.random.randn(512).astype(np.float32),
    )
    large = DetectedFace(
        bbox=np.array([0, 0, 50, 50], dtype=np.float32),
        score=0.9,
        embedding=np.random.randn(512).astype(np.float32),
    )
    low_score = DetectedFace(
        bbox=np.array([0, 0, 80, 80], dtype=np.float32),
        score=0.5,
        embedding=np.random.randn(512).astype(np.float32),
    )
    assert not proc._passes_quality(small)
    assert proc._passes_quality(large)
    assert not proc._passes_quality(low_score)
    print("face_processor quality gates OK")


if __name__ == "__main__":
    main()
