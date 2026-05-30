"""Sync identity API employees into edge ``visitors`` gallery rows."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from edge_ai.pipeline.store import META_PERSON_ID, META_PERSON_KIND, PersonGalleryStore
from shared.config import Settings
from shared.database.models import Visitor
from shared.database.repository import AnalyticsRepository
from shared.tenant_resolve import resolve_brand_id

META_EMPLOYEE_ID = "employee_id"


def find_employee_visitor(
    db: Session,
    settings: Settings,
    brand_id: uuid.UUID,
    employee_id: uuid.UUID,
) -> Optional[Visitor]:
    repo = AnalyticsRepository(db, settings, brand_id)
    key = str(employee_id)
    for visitor in repo.list_visitors_with_embeddings():
        meta = visitor.metadata_ or {}
        if meta.get(META_EMPLOYEE_ID) == key:
            return visitor
    return None


def upsert_employee_visitor(
    db: Session,
    settings: Settings,
    *,
    employee_id: uuid.UUID,
    name: str,
    embedding: list[float],
) -> Visitor:
    """Create or update Visitor row for edge pipeline employee matching."""
    brand_id = resolve_brand_id(db, settings)
    store = PersonGalleryStore(db, settings, brand_id)
    visitor = find_employee_visitor(db, settings, brand_id, employee_id)
    if visitor is None:
        visitor = store.register_employee(embedding, employee_code=name)
        meta = dict(visitor.metadata_ or {})
        meta[META_EMPLOYEE_ID] = str(employee_id)
        visitor.metadata_ = meta
    else:
        store.update_embedding(visitor, embedding)
        visitor.display_name = name
        meta = dict(visitor.metadata_ or {})
        meta[META_EMPLOYEE_ID] = str(employee_id)
        meta[META_PERSON_KIND] = "employee"
        visitor.metadata_ = meta
    db.flush()
    return visitor
