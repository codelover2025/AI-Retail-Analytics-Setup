"""Per-frame CV + identity without DB commits (batch flush handled by worker)."""

from __future__ import annotations

import logging
import threading
import uuid
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from edge_ai.pipeline.face_processor import FaceProcessor
from edge_ai.pipeline.identity_service import IdentityService
from edge_ai.pipeline.track_embedding_buffer import TrackEmbeddingAccumulator
from edge_ai.pipeline.types import IdentityEvent
from edge_ai.analytics.types import FramePerson, utcnow
from edge_ai.tracking.byte_tracker import FaceTracker
from shared.config import Settings

logger = logging.getLogger(__name__)


class InMemoryFrameProcessor:
    """
    Detection → track → identity for one camera.

    Uses shared FaceProcessor + lock across cameras in a worker group.
    Gallery loaded once; ``refresh_gallery=False`` during hot loop.
    """

    def __init__(
        self,
        *,
        camera_id: str,
        settings: Settings,
        brand_id: uuid.UUID,
        db: Session,
        face_processor: FaceProcessor,
        detector_lock: threading.Lock,
        identity_service: Optional[IdentityService] = None,
    ):
        self.camera_id = camera_id
        self.settings = settings
        self.brand_id = brand_id
        self.db = db
        self.face_processor = face_processor
        self._detector_lock = detector_lock
        self.tracker = FaceTracker()
        self._track_embeds = TrackEmbeddingAccumulator(
            min_frames=settings.track_embed_min_frames,
            max_frames=settings.track_embed_max_frames,
        )
        self._identity = identity_service or IdentityService(
            db,
            settings,
            brand_id,
            refresh_gallery=True,
        )
        self._visit_tracks: set[int] = set()

    @property
    def identity(self) -> IdentityService:
        return self._identity

    def process(
        self,
        frame: np.ndarray,
        *,
        timestamp=None,
    ) -> list[FramePerson]:
        ts = timestamp or utcnow()
        with self._detector_lock:
            detections = self.face_processor.process_frame(frame)
        if self.settings.max_faces_per_frame > 0:
            detections = sorted(detections, key=lambda d: d.score, reverse=True)[
                : self.settings.max_faces_per_frame
            ]

        tracked = self.tracker.update(detections)
        active_tracks = {face.track_id for face in tracked}
        self._track_embeds.prune_inactive(active_tracks)
        for tid in list(self._identity._track_person):
            if tid not in active_tracks:
                self._identity.clear_track(tid)

        persons: list[FramePerson] = []
        for face in tracked:
            embed, stable = self._track_embeds.update(face.track_id, face.embedding)
            if not stable and face.track_id not in self._visit_tracks:
                continue

            event = self._identity.resolve(
                face.track_id,
                embed,
                camera_id=self.camera_id,
                detection_score=face.score,
            )
            self._visit_tracks.add(face.track_id)
            persons.append(
                FramePerson(
                    person_id=event.person_id,
                    track_id=face.track_id,
                    camera_id=self.camera_id,
                    bbox=face.bbox.tolist(),
                    identity_type=event.type,
                    timestamp=ts,
                )
            )
        return persons

    def pending_db_flush(self) -> None:
        """Flush ORM session without closing (called on batch interval)."""
        try:
            self.db.flush()
        except Exception:
            logger.exception("DB flush failed for camera %s", self.camera_id)
