"""Identity resolution: match → person_id → visitor type (new / repeat / employee)."""

from __future__ import annotations

import logging
import uuid
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from edge_ai.embeddings.face_embedder import FaceEmbedder
from edge_ai.pipeline.matcher import CosineMatcher, GalleryEntry, MatchHit
from edge_ai.pipeline.store import (
    META_PERSON_ID,
    PersonGalleryStore,
    person_id_from_visitor,
    person_kind_from_visitor,
)
from edge_ai.pipeline.types import (
    PERSON_KIND_CUSTOMER,
    PERSON_KIND_EMPLOYEE,
    IdentityEvent,
    IdentityType,
    utcnow,
)
from shared.config import Settings

logger = logging.getLogger(__name__)


class IdentityService:
    """
    Camera → embed → match → person_id.

    Rules:
    - Employee gallery checked first; match → ``employee``.
    - No gallery match → new ``person_id``, ``new_visitor``.
    - Gallery match + ``visit_count > 1`` → ``repeat_visitor``.
    - Gallery match otherwise → ``visitor`` (known customer, not yet repeat).
    - Per-track cache avoids duplicate gallery scans.
    """

    def __init__(
        self,
        db: Session,
        settings: Settings,
        brand_id: uuid.UUID,
        *,
        matcher: Optional[CosineMatcher] = None,
        refresh_gallery: bool = True,
        track_person: Optional[dict[int, int]] = None,
        track_visitor_uuid: Optional[dict[int, uuid.UUID]] = None,
    ):
        self.settings = settings
        self.store = PersonGalleryStore(db, settings, brand_id)
        threshold = settings.recognition_threshold
        if threshold < 0.5 or threshold > 0.6:
            logger.info(
                "recognition_threshold=%.2f outside recommended 0.5–0.6",
                threshold,
            )
        self.matcher = matcher or CosineMatcher(
            threshold=threshold,
            cache_recent=True,
        )
        if refresh_gallery:
            self.refresh_gallery()
        self._track_person = track_person if track_person is not None else {}
        self._track_visitor_uuid = (
            track_visitor_uuid if track_visitor_uuid is not None else {}
        )

    def refresh_gallery(self) -> None:
        entries = self.store.load_entries()
        self.matcher.load_gallery(entries)
        logger.debug("Identity gallery loaded: %d entries", len(entries))

    def resolve(
        self,
        track_id: int,
        embedding: np.ndarray,
        *,
        camera_id: str,
        detection_score: float = 0.0,
    ) -> IdentityEvent:
        """
        Resolve identity for one tracked face.

        Returns structured event; persists new persons via store.
        """
        if track_id in self._track_person:
            visitor = self.store.get_visitor(self._track_visitor_uuid[track_id])
            if visitor is None:
                self._clear_track(track_id)
            else:
                return self._event_from_visitor(
                    visitor,
                    identity_type=self._identity_type_for_visitor(visitor),
                    camera_id=camera_id,
                    match_score=1.0,
                    is_new_person=False,
                )

        normed = FaceEmbedder.from_detection(embedding)
        embedding_list = FaceEmbedder.to_list(normed)

        employee_hit = self.matcher.match_employee(normed)
        if employee_hit is not None:
            return self._resolve_hit(
                employee_hit,
                embedding_list=embedding_list,
                track_id=track_id,
                camera_id=camera_id,
                detection_score=detection_score,
                force_type="employee",
            )

        customer_hit = self.matcher.match_customer(normed)
        if customer_hit is not None:
            return self._resolve_hit(
                customer_hit,
                embedding_list=embedding_list,
                track_id=track_id,
                camera_id=camera_id,
                detection_score=detection_score,
            )

        return self._register_new_person(
            embedding_list=embedding_list,
            track_id=track_id,
            camera_id=camera_id,
            detection_score=detection_score,
        )

    def clear_track(self, track_id: int) -> None:
        self._clear_track(track_id)

    def _resolve_hit(
        self,
        hit: MatchHit,
        *,
        embedding_list: list[float],
        track_id: int,
        camera_id: str,
        detection_score: float,
        force_type: Optional[IdentityType] = None,
    ) -> IdentityEvent:
        visitor_id = uuid.UUID(hit.visitor_id) if hit.visitor_id else None
        visitor = self.store.get_visitor(visitor_id) if visitor_id else None

        if visitor is None:
            logger.warning(
                "Gallery hit person_id=%s missing visitor row; re-registering",
                hit.person_id,
            )
            return self._register_new_person(
                embedding_list=embedding_list,
                track_id=track_id,
                camera_id=camera_id,
                detection_score=detection_score,
            )

        self._bind_track(track_id, visitor)
        self.matcher.add_entry(
            GalleryEntry(
                person_id=hit.person_id,
                embedding=np.array(embedding_list, dtype=np.float32),
                person_kind=person_kind_from_visitor(visitor),  # type: ignore[arg-type]
                visitor_id=str(visitor.id),
            )
        )

        if force_type == "employee":
            identity_type: IdentityType = "employee"
        else:
            identity_type = self._identity_type_for_visitor(visitor)

        return self._event_from_visitor(
            visitor,
            identity_type=identity_type,
            camera_id=camera_id,
            match_score=hit.score,
            is_new_person=False,
        )

    def _register_new_person(
        self,
        *,
        embedding_list: list[float],
        track_id: int,
        camera_id: str,
        detection_score: float,
    ) -> IdentityEvent:
        visitor = self.store.register_person(
            embedding_list,
            person_kind=PERSON_KIND_CUSTOMER,
        )
        person_id = person_id_from_visitor(visitor)
        self.store.repo.increment_unique_footfall(self.settings.store_id)
        self._bind_track(track_id, visitor)
        self.matcher.add_entry(
            GalleryEntry(
                person_id=person_id,
                embedding=np.array(embedding_list, dtype=np.float32),
                person_kind=PERSON_KIND_CUSTOMER,
                visitor_id=str(visitor.id),
            )
        )
        logger.info(
            "New person_id=%s visitor=%s score=%.2f",
            person_id,
            visitor.id,
            detection_score,
        )
        return self._event_from_visitor(
            visitor,
            identity_type="new_visitor",
            camera_id=camera_id,
            match_score=0.0,
            is_new_person=True,
        )

    def _bind_track(self, track_id: int, visitor: object) -> None:
        from shared.database.models import Visitor

        assert isinstance(visitor, Visitor)
        self._track_person[track_id] = person_id_from_visitor(visitor)
        self._track_visitor_uuid[track_id] = visitor.id

    def _clear_track(self, track_id: int) -> None:
        self._track_person.pop(track_id, None)
        self._track_visitor_uuid.pop(track_id, None)

    @staticmethod
    def _identity_type_for_visitor(visitor: object) -> IdentityType:
        """
        Classify using persisted visit_count (evaluated before record_visit in pipeline).

        - employee → ``employee``
        - visit_count > 1 → ``repeat_visitor``
        - gallery match with visit_count <= 1 → ``visitor``
        """
        if person_kind_from_visitor(visitor) == PERSON_KIND_EMPLOYEE:
            return "employee"
        if visitor.visit_count > 1:
            return "repeat_visitor"
        return "visitor"

    def _event_from_visitor(
        self,
        visitor: object,
        *,
        identity_type: IdentityType,
        camera_id: str,
        match_score: float,
        is_new_person: bool,
    ) -> IdentityEvent:
        from shared.database.models import Visitor

        assert isinstance(visitor, Visitor)
        return IdentityEvent(
            person_id=person_id_from_visitor(visitor),
            type=identity_type,
            camera_id=camera_id,
            timestamp=utcnow(),
            visitor_id=visitor.id,
            match_score=match_score,
            is_new_person=is_new_person,
        )

    def should_count_unique_footfall(self, event: IdentityEvent) -> bool:
        """Employees do not increment unique customer footfall."""
        return event.type != "employee" and event.is_new_person
