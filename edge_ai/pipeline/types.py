"""Structured identity outputs from the edge recognition pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
import uuid

IdentityType = Literal["new_visitor", "visitor", "repeat_visitor", "employee", "watchlist"]

PERSON_KIND_CUSTOMER = "customer"
PERSON_KIND_EMPLOYEE = "employee"
EMBEDDING_DIM = 512


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ProcessedFace:
    """Single face passing quality gates, ready for matching."""

    bbox: list[float]
    score: float
    embedding: Any  # np.ndarray — avoid hard numpy import in types
    track_id: int | None = None


@dataclass
class IdentityEvent:
    """
    Canonical pipeline output (embeddings only — no video).

    person_id: stable integer per brand (stored in Visitor.metadata).
  """

    person_id: int
    type: IdentityType
    camera_id: str
    timestamp: datetime
    visitor_id: uuid.UUID
    match_score: float
    is_new_person: bool

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["visitor_id"] = str(self.visitor_id)
        return data
