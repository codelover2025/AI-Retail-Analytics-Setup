import uuid
from dataclasses import dataclass
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from edge_ai.pipeline.identity_service import IdentityService
from edge_ai.pipeline.types import IdentityEvent
from shared.config import Settings
from shared.database.models import Visitor


@dataclass
class MatchResult:
    visitor: Visitor
    confidence: float
    is_new: bool
    identity: Optional[IdentityEvent] = None


class FaceMatcher:
    """
    Backward-compatible wrapper around :class:`IdentityService`.
    Prefer ``IdentityService`` for new code.
    """

    def __init__(self, db: Session, settings: Settings, brand_id: uuid.UUID):
        self._service = IdentityService(db, settings, brand_id)

    def identify(
        self,
        track_id: int,
        embedding: np.ndarray,
        *,
        camera_id: Optional[str] = None,
        detection_score: float = 0.0,
    ) -> MatchResult:
        event = self._service.resolve(
            track_id,
            embedding,
            camera_id=camera_id or self._service.settings.camera_id,
            detection_score=detection_score,
        )
        visitor = self._service.store.get_visitor(event.visitor_id)
        if visitor is None:
            raise RuntimeError(f"Visitor missing after identity resolve: {event.visitor_id}")
        return MatchResult(
            visitor=visitor,
            confidence=event.match_score if not event.is_new_person else detection_score,
            is_new=event.is_new_person,
            identity=event,
        )

    def should_count_unique_footfall(self, result: MatchResult) -> bool:
        if result.identity is None:
            return result.is_new
        return self._service.should_count_unique_footfall(result.identity)

    def clear_track(self, track_id: int) -> None:
        self._service.clear_track(track_id)
