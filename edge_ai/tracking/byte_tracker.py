from dataclasses import dataclass
from typing import Optional

import numpy as np

from edge_ai.detection.face_detector import DetectedFace


@dataclass
class TrackedFace:
    track_id: int
    bbox: np.ndarray
    score: float
    embedding: np.ndarray
    detection: DetectedFace


class FaceTracker:
    """ByteTrack wrapper via supervision for stable track IDs."""

    def __init__(self):
        self._tracker = None

    def _ensure_tracker(self) -> None:
        if self._tracker is not None:
            return
        from supervision import ByteTrack

        self._tracker = ByteTrack()

    def update(self, detections: list[DetectedFace]) -> list[TrackedFace]:
        self._ensure_tracker()
        assert self._tracker is not None

        if not detections:
            self._tracker.update_with_detections(self._empty_sv_detections())
            return []

        import supervision as sv

        xyxy = np.array([d.bbox for d in detections], dtype=np.float32)
        confidence = np.array([d.score for d in detections], dtype=np.float32)
        sv_det = sv.Detections(xyxy=xyxy, confidence=confidence)
        tracked = self._tracker.update_with_detections(sv_det)

        results: list[TrackedFace] = []
        if tracked.tracker_id is None:
            return results

        for i, track_id in enumerate(tracked.tracker_id):
            if track_id is None:
                continue
            det_idx = self._match_detection_index(tracked.xyxy[i], detections)
            if det_idx is None:
                continue
            det = detections[det_idx]
            conf = (
                float(tracked.confidence[i])
                if tracked.confidence is not None
                else det.score
            )
            results.append(
                TrackedFace(
                    track_id=int(track_id),
                    bbox=tracked.xyxy[i].astype(np.float32),
                    score=conf,
                    embedding=det.embedding,
                    detection=det,
                )
            )
        return results

    @staticmethod
    def _empty_sv_detections():
        import supervision as sv

        return sv.Detections(
            xyxy=np.empty((0, 4), dtype=np.float32),
            confidence=np.empty((0,), dtype=np.float32),
        )

    @staticmethod
    def _match_detection_index(
        bbox: np.ndarray, detections: list[DetectedFace]
    ) -> Optional[int]:
        best_iou = 0.0
        best_idx: Optional[int] = None
        for i, det in enumerate(detections):
            iou = FaceTracker._iou(bbox, det.bbox)
            if iou > best_iou:
                best_iou = iou
                best_idx = i
        return best_idx if best_iou > 0.3 else None

    @staticmethod
    def _iou(a: np.ndarray, b: np.ndarray) -> float:
        x1 = max(a[0], b[0])
        y1 = max(a[1], b[1])
        x2 = min(a[2], b[2])
        y2 = min(a[3], b[3])
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        area_a = (a[2] - a[0]) * (a[3] - a[1])
        area_b = (b[2] - b[0]) * (b[3] - b[1])
        union = area_a + area_b - inter + 1e-6
        return inter / union
