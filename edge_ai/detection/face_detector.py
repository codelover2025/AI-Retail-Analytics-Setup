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

    def __init__(self, det_size: int = 640, ctx_id: int | None = None):
        from shared.config import get_settings

        settings = get_settings()
        self.det_size = det_size
        self.ctx_id = ctx_id if ctx_id is not None else settings.insightface_ctx_id
        self._app = None

    def _ensure_model(self) -> None:
        if self._app is not None:
            return
        from insightface.app import FaceAnalysis

        kwargs: dict = {
            "name": "buffalo_l",
            "allowed_modules": ["detection", "recognition"],
        }
        providers = self._onnx_providers()
        try:
            if providers:
                self._app = FaceAnalysis(providers=providers, **kwargs)
            else:
                self._app = FaceAnalysis(**kwargs)
        except TypeError:
            self._app = FaceAnalysis(**kwargs)
        self._app.prepare(ctx_id=self.ctx_id, det_size=(self.det_size, self.det_size))
        device = "GPU" if self.ctx_id >= 0 else "CPU"
        logger.info("InsightFace model loaded (buffalo_l, %s, ctx_id=%s)", device, self.ctx_id)

    @staticmethod
    def _onnx_providers() -> list[str] | None:
        try:
            import onnxruntime as ort

            available = ort.get_available_providers()
            providers = []
            
            # 1. Prefer TensorRT if available
            if "TensorrtExecutionProvider" in available:
                providers.append("TensorrtExecutionProvider")
            # 2. CUDA fallback
            if "CUDAExecutionProvider" in available:
                providers.append("CUDAExecutionProvider")
                
            providers.append("CPUExecutionProvider")
            
            # Log selected providers
            logger.info("Configured ONNX Execution Providers: %s", providers)
            return providers
        except Exception as exc:
            logger.warning("Error resolving ONNX providers: %s", exc)
        return None

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
