"""Load/sync person gallery from DB (embeddings only). No API layer."""

from __future__ import annotations

import uuid
from typing import Any, Optional

import numpy as np
from sqlalchemy.orm import Session

from edge_ai.embeddings.face_embedder import EMBEDDING_DIM, INSIGHTFACE_MODEL
from edge_ai.pipeline.matcher import GalleryEntry
from edge_ai.pipeline.types import PERSON_KIND_CUSTOMER, PERSON_KIND_EMPLOYEE
from shared.config import Settings
from shared.database.models import Visitor
from shared.database.repository import AnalyticsRepository

META_PERSON_ID = "person_id"
META_PERSON_KIND = "person_kind"
META_EMBEDDING_MODEL = "embedding_model"
META_EMBEDDING_DIM = "embedding_dim"


def person_id_from_visitor(visitor: Visitor) -> int:
    meta: dict[str, Any] = visitor.metadata_ or {}
    if META_PERSON_ID in meta:
        return int(meta[META_PERSON_ID])
    # Stable fallback for legacy rows without person_id
    return int(visitor.id.int % (10**9))


def person_kind_from_visitor(visitor: Visitor) -> str:
    meta: dict[str, Any] = visitor.metadata_ or {}
    return str(meta.get(META_PERSON_KIND, PERSON_KIND_CUSTOMER))


class PersonGalleryStore:
    """Bridges SQLAlchemy visitors ↔ in-memory matcher gallery."""

    def __init__(self, db: Session, settings: Settings, brand_id: uuid.UUID):
        self.repo = AnalyticsRepository(db, settings, brand_id)
        self.db = db
        self.settings = settings
        self.brand_id = brand_id

    def load_entries(self) -> list[GalleryEntry]:
        entries: list[GalleryEntry] = []
        for visitor in self.repo.list_visitors_with_embeddings():
            emb = np.array(visitor.embedding, dtype=np.float32)
            entries.append(
                GalleryEntry(
                    person_id=person_id_from_visitor(visitor),
                    embedding=emb,
                    person_kind=person_kind_from_visitor(visitor),  # type: ignore[arg-type]
                    visitor_id=str(visitor.id),
                )
            )
        return entries

    def get_visitor(self, visitor_id: uuid.UUID) -> Optional[Visitor]:
        return self.db.get(Visitor, visitor_id)

    def allocate_person_id(self, visitor_uuid: uuid.UUID) -> int:
        return int(visitor_uuid.int % (10**9))

    def register_person(
        self,
        embedding: list[float],
        *,
        person_kind: str = PERSON_KIND_CUSTOMER,
        display_name: Optional[str] = None,
    ) -> Visitor:
        visitor = self.repo.register_visitor(
            embedding=embedding,
            display_name="",
        )
        person_id = self.allocate_person_id(visitor.id)
        if display_name is None:
            display_name = f"Person-{person_id}"
        visitor.display_name = display_name
        visitor.metadata_ = {
            META_PERSON_ID: person_id,
            META_PERSON_KIND: person_kind,
            META_EMBEDDING_MODEL: INSIGHTFACE_MODEL,
            META_EMBEDDING_DIM: EMBEDDING_DIM,
        }
        self.db.flush()
        return visitor

    def update_embedding(self, visitor: Visitor, embedding: list[float]) -> None:
        visitor.embedding = embedding
        self.db.flush()

    def register_employee(
        self,
        embedding: list[float],
        *,
        employee_code: str,
    ) -> Visitor:
        return self.register_person(
            embedding,
            person_kind=PERSON_KIND_EMPLOYEE,
            display_name=employee_code,
        )
