"""Structured analytics outputs (no API layer)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class FramePerson:
    """One tracked person in a single processed frame."""

    person_id: int
    track_id: int
    camera_id: str
    bbox: list[float]
    identity_type: str  # new_visitor | visitor | repeat_visitor | employee
    timestamp: datetime


@dataclass
class AnalyticsSessionRecord:
    """Completed or active visit session for one person on one camera."""

    person_id: int
    camera_id: str
    entry_time: datetime
    exit_time: datetime | None = None
    dwell_time: float | None = None
    zones: list[str] = field(default_factory=list)
    zone_time: dict[str, float] = field(default_factory=dict)
    interaction: bool = False
    identity_type: str = "visitor"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["entry_time"] = self.entry_time.isoformat()
        if self.exit_time is not None:
            data["exit_time"] = self.exit_time.isoformat()
        return data
