import numpy as np

from edge_ai.detection.face_detector import DetectedFace


class MockFaceDetector:
    """Deterministic fake detections for local/CI testing without InsightFace."""

    def __init__(self, faces_per_frame: int = 1):
        self.faces_per_frame = faces_per_frame
        self._rng = np.random.default_rng(42)

    def detect(self, frame: np.ndarray) -> list[DetectedFace]:
        h, w = frame.shape[:2]
        results: list[DetectedFace] = []
        for i in range(self.faces_per_frame):
            cx = w * (0.35 + 0.2 * i)
            cy = h * 0.45
            size = min(w, h) * 0.18
            bbox = np.array(
                [cx - size, cy - size, cx + size, cy + size],
                dtype=np.float32,
            )
            embedding = self._rng.standard_normal(512).astype(np.float32)
            embedding /= np.linalg.norm(embedding) + 1e-8
            results.append(
                DetectedFace(
                    bbox=bbox,
                    score=0.99,
                    embedding=embedding,
                )
            )
        return results
