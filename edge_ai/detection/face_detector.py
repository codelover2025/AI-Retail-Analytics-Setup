import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DetectedFace:
    bbox: np.ndarray  # [x1, y1, x2, y2]
    score: float
    embedding: np.ndarray
    landmarks: Optional[np.ndarray] = None


class FaceDetector:
    """InsightFace-based face detection and embedding extraction."""

    def __init__(self, det_size: int = 640, ctx_id: int = 0):
        self.det_size = det_size
        self.ctx_id = ctx_id
        self._app = None

    def _ensure_model(self) -> None:
        if self._app is not None:
            return
        from insightface.app import FaceAnalysis

        self._app = FaceAnalysis(
            name="buffalo_l",
            allowed_modules=["detection", "recognition"],
        )
        self._app.prepare(ctx_id=self.ctx_id, det_size=(self.det_size, self.det_size))
        logger.info("InsightFace model loaded (buffalo_l)")

    def detect(self, frame: np.ndarray) -> list[DetectedFace]:
        self._ensure_model()
        assert self._app is not None

        faces = self._app.get(frame)
        results: list[DetectedFace] = []
        for face in faces:
            if face.det_score < 0.5:
                continue
            bbox = face.bbox.astype(np.float32)
            embedding = face.normed_embedding.astype(np.float32)
            landmarks = getattr(face, "kps", None)
            results.append(
                DetectedFace(
                    bbox=bbox,
                    score=float(face.det_score),
                    embedding=embedding,
                    landmarks=landmarks,
                )
            )
        return results
