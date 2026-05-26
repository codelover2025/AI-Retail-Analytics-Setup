"""InsightFace detection + 512-d embedding extraction with quality gates."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from edge_ai.detection.face_detector import DetectedFace, FaceDetector
from edge_ai.embeddings.face_embedder import normalize_embedding
from edge_ai.pipeline.types import EMBEDDING_DIM

if TYPE_CHECKING:
    from shared.config import Settings

logger = logging.getLogger(__name__)


class FaceProcessor:
    """
    Wraps InsightFace (buffalo_l): detection + recognition modules.
    Drops faces below min_confidence (default 0.6). No video persistence.
    """

    def __init__(
        self,
        *,
        min_confidence: float = 0.6,
        min_bbox_area: float = 1600.0,
        det_size: int = 640,
        ctx_id: int | None = None,
    ):
        self.min_confidence = min_confidence
        self.min_bbox_area = min_bbox_area
        self.detector = FaceDetector(det_size=det_size, ctx_id=ctx_id)

    @classmethod
    def from_settings(cls, settings: Settings) -> FaceProcessor:
        return cls(
            min_confidence=settings.min_face_score,
            min_bbox_area=settings.min_bbox_area,
            det_size=settings.det_size,
            ctx_id=settings.insightface_ctx_id,
        )

    def process_frame(self, frame: np.ndarray) -> list[DetectedFace]:
        """Detect faces; return only 512-d normalized embeddings above min_confidence."""
        raw = self.detector.detect(frame)
        return [self._normalize_face(face) for face in raw if self._passes_quality(face)]

    @staticmethod
    def bbox_area(bbox: np.ndarray) -> float:
        x1, y1, x2, y2 = bbox[:4]
        return float(max(0.0, x2 - x1) * max(0.0, y2 - y1))

    def _passes_quality(self, face: DetectedFace) -> bool:
        if face.score < self.min_confidence:
            return False
        if self.bbox_area(face.bbox) < self.min_bbox_area:
            logger.debug(
                "Skipping face: bbox area %.0f < min %.0f",
                self.bbox_area(face.bbox),
                self.min_bbox_area,
            )
            return False
        emb = np.asarray(face.embedding, dtype=np.float32)
        if emb.size != EMBEDDING_DIM:
            logger.debug("Skipping face: embedding dim %s != %s", emb.size, EMBEDDING_DIM)
            return False
        return True

    def _normalize_face(self, face: DetectedFace) -> DetectedFace:
        emb = normalize_embedding(np.asarray(face.embedding, dtype=np.float32))
        return DetectedFace(
            bbox=face.bbox.astype(np.float32),
            score=float(face.score),
            embedding=emb,
            landmarks=face.landmarks,
        )
