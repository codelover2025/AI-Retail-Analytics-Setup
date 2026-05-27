"""Extract face embeddings from uploaded images (InsightFace)."""

from __future__ import annotations

import logging
from typing import BinaryIO

import numpy as np

from edge_ai.embeddings.face_embedder import EMBEDDING_DIM, FaceEmbedder
from edge_ai.pipeline.face_processor import FaceProcessor

logger = logging.getLogger(__name__)

_detector: FaceProcessor | None = None


def _processor() -> FaceProcessor:
    global _detector
    if _detector is None:
        from shared.config import get_settings

        _detector = FaceProcessor.from_settings(get_settings())
    return _detector


def _read_image(data: bytes) -> np.ndarray:
    import cv2

    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image (use JPEG or PNG)")
    return img


def embeddings_from_image_bytes(
    data: bytes,
    *,
    min_confidence: float | None = None,
) -> list[np.ndarray]:
    """Return one normalized embedding per face detected in the image."""
    proc = _processor()
    if min_confidence is not None:
        proc.min_confidence = min_confidence
    frame = _read_image(data)
    faces = proc.process_frame(frame)
    if not faces:
        raise ValueError("No face detected in image")
    return [FaceEmbedder.from_detection(f.embedding) for f in faces]


def embedding_from_upload(
    files: list[BinaryIO | bytes],
    *,
    min_similarity: float | None = None,
) -> list[float]:
    """
    Mean embedding from 1–N images (uses largest face per image if multiple).
    """
    from shared.config import get_settings

    settings = get_settings()
    sim = min_similarity if min_similarity is not None else settings.enrollment_frame_similarity
    collected: list[np.ndarray] = []
    for item in files:
        raw = item.read() if hasattr(item, "read") else item
        if not raw:
            continue
        embs = embeddings_from_image_bytes(raw)
        collected.append(embs[0])
    if not collected:
        raise ValueError("No valid images with detectable faces")
    mean = FaceEmbedder.enroll_from_frames(collected, min_similarity=sim)
    if mean.shape[0] != EMBEDDING_DIM:
        raise ValueError(f"Invalid embedding dimension {mean.shape[0]}")
    return FaceEmbedder.to_list(mean)
