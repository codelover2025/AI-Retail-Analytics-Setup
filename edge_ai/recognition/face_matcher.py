import uuid
from dataclasses import dataclass
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from edge_ai.embeddings.face_embedder import FaceEmbedder
from shared.config import Settings
from shared.database.models import Visitor
from shared.database.repository import AnalyticsRepository


@dataclass
class MatchResult:
    visitor: Visitor
    confidence: float
    is_new: bool


class FaceMatcher:
    """Cosine-similarity face recognition against stored visitor embeddings."""

    def __init__(self, db: Session, settings: Settings, brand_id):
        self.repo = AnalyticsRepository(db, settings, brand_id)
        self.settings = settings
        self._track_visitor: dict[int, uuid.UUID] = {}

    def identify(
        self,
        track_id: int,
        embedding: np.ndarray,
    ) -> MatchResult:
        if track_id in self._track_visitor:
            visitor = self.repo.db.get(Visitor, self._track_visitor[track_id])
            if visitor:
                return MatchResult(visitor=visitor, confidence=1.0, is_new=False)

        normed = FaceEmbedder.from_detection(embedding)
        match, score = self.repo.find_best_match(normed)

        if match is not None:
            self._track_visitor[track_id] = match.id
            return MatchResult(visitor=match, confidence=score, is_new=False)

        visitor = self.repo.register_visitor(
            embedding=FaceEmbedder.to_list(normed),
            display_name=f"Visitor-{str(uuid.uuid4())[:8]}",
        )
        self.repo.increment_unique_footfall(self.settings.store_id)
        self._track_visitor[track_id] = visitor.id
        return MatchResult(visitor=visitor, confidence=score, is_new=True)

    def clear_track(self, track_id: int) -> None:
        self._track_visitor.pop(track_id, None)
