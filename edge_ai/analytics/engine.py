"""In-memory analytics engine — entry/exit, dwell, zones, interactions."""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from edge_ai.analytics.interaction import interactions_by_zone
from edge_ai.analytics.session_tracker import SessionTracker
from edge_ai.analytics.types import AnalyticsSessionRecord, FramePerson, utcnow
from edge_ai.analytics.zones import CameraZones, bbox_centroid, load_zones, zones_for_centroid

logger = logging.getLogger(__name__)

OnSessionComplete = Callable[[AnalyticsSessionRecord], None]


class AnalyticsEngine:
    """Aggregates per-frame person updates into structured session records."""

    def __init__(
        self,
        settings,
        *,
        on_session_complete: OnSessionComplete | None = None,
        output_path: str | Path | None = None,
    ):
        self.settings = settings
        self._zones: dict[str, CameraZones] = load_zones(settings)
        self._sessions = SessionTracker(
            exit_timeout_seconds=settings.analytics_exit_timeout_seconds
        )
        self._on_complete = on_session_complete
        self._output_path = Path(output_path) if output_path else None
        self._lock = threading.Lock()
        if self._output_path:
            self._output_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def zones(self) -> dict[str, CameraZones]:
        return self._zones

    def process_frame(
        self,
        persons: list[FramePerson],
    ) -> list[AnalyticsSessionRecord]:
        """Update sessions from one processed frame; return newly completed sessions."""
        with self._lock:
            return self._process_frame_unlocked(persons)

    def _process_frame_unlocked(
        self,
        persons: list[FramePerson],
    ) -> list[AnalyticsSessionRecord]:
        if not persons:
            return self._sessions.flush_timeouts()

        person_zones: dict[int, list[str]] = {}
        for p in persons:
            cam_zones = self._zones.get(p.camera_id)
            if cam_zones is None:
                person_zones[p.person_id] = []
            else:
                person_zones[p.person_id] = zones_for_centroid(
                    bbox_centroid(p.bbox), cam_zones
                )

        interacting = interactions_by_zone(persons, person_zones)
        for p in persons:
            self._sessions.update_person(
                p,
                person_zones.get(p.person_id, []),
                interaction=p.person_id in interacting,
            )

        completed = self._sessions.flush_timeouts(now=persons[0].timestamp)
        for record in completed:
            self._emit(record)
        return completed

    def tick(self) -> list[AnalyticsSessionRecord]:
        """Periodic timeout sweep (call when no frames arrive)."""
        with self._lock:
            completed = self._sessions.flush_timeouts(now=utcnow())
            for record in completed:
                self._emit(record)
            return completed

    def flush_all(self) -> list[AnalyticsSessionRecord]:
        """Force-close all active sessions (shutdown)."""
        with self._lock:
            completed: list[AnalyticsSessionRecord] = []
            for snap in self._sessions.active_snapshot():
                snap.exit_time = utcnow()
                snap.dwell_time = (snap.exit_time - snap.entry_time).total_seconds()
                completed.append(snap)
                self._emit(snap)
            self._sessions._active.clear()
            return completed

    def _emit(self, record: AnalyticsSessionRecord) -> None:
        logger.info("analytics session %s", json.dumps(record.to_dict()))
        if self._on_complete:
            self._on_complete(record)
        if self._output_path:
            with self._output_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record.to_dict()) + "\n")

    def stats(self) -> dict[str, Any]:
        with self._lock:
            active = self._sessions.active_snapshot()
            return {
                "active_sessions": len(active),
                "cameras_with_zones": len(self._zones),
            }
