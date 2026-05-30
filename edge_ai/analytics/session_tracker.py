"""Entry/exit sessions and dwell time per camera (in-memory)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from edge_ai.analytics.types import AnalyticsSessionRecord, FramePerson, utcnow


@dataclass
class _ActiveSession:
    person_id: int
    camera_id: str
    identity_type: str
    entry_time: datetime
    last_seen: datetime
    zones_visited: set[str] = field(default_factory=set)
    zone_time: dict[str, float] = field(default_factory=dict)
    zone_entered_at: dict[str, datetime] = field(default_factory=dict)
    interaction: bool = False


class SessionTracker:
    """
    active_sessions[camera_id][person_id] = entry_time semantics via _ActiveSession.

    Exit when not seen for ``exit_timeout_seconds``.
    """

    def __init__(self, *, exit_timeout_seconds: float = 4.0):
        self.exit_timeout_seconds = exit_timeout_seconds
        self._active: dict[str, dict[int, _ActiveSession]] = {}

    def update_person(
        self,
        person: FramePerson,
        zones: list[str],
        *,
        interaction: bool = False,
    ) -> None:
        cam = person.camera_id
        pid = person.person_id
        now = person.timestamp
        by_cam = self._active.setdefault(cam, {})
        session = by_cam.get(pid)
        if session is None:
            session = _ActiveSession(
                person_id=pid,
                camera_id=cam,
                identity_type=person.identity_type,
                entry_time=now,
                last_seen=now,
            )
            by_cam[pid] = session

        session.last_seen = now
        session.identity_type = person.identity_type
        if interaction:
            session.interaction = True

        current_zone_set = set(zones)
        for z in zones:
            session.zones_visited.add(z)
            if z not in session.zone_entered_at:
                session.zone_entered_at[z] = now

        for z, entered in list(session.zone_entered_at.items()):
            if z not in current_zone_set:
                session.zone_time[z] = session.zone_time.get(z, 0.0) + (
                    now - entered
                ).total_seconds()
                del session.zone_entered_at[z]

    def flush_timeouts(self, *, now: datetime | None = None) -> list[AnalyticsSessionRecord]:
        now = now or utcnow()
        completed: list[AnalyticsSessionRecord] = []
        for cam, by_person in list(self._active.items()):
            for pid, session in list(by_person.items()):
                if (now - session.last_seen).total_seconds() < self.exit_timeout_seconds:
                    continue
                for z, entered in session.zone_entered_at.items():
                    session.zone_time[z] = session.zone_time.get(z, 0.0) + (
                        now - entered
                    ).total_seconds()
                exit_time = session.last_seen
                dwell = (exit_time - session.entry_time).total_seconds()
                completed.append(
                    AnalyticsSessionRecord(
                        person_id=session.person_id,
                        camera_id=session.camera_id,
                        entry_time=session.entry_time,
                        exit_time=exit_time,
                        dwell_time=dwell,
                        zones=sorted(session.zones_visited),
                        zone_time=dict(session.zone_time),
                        interaction=session.interaction,
                        identity_type=session.identity_type,
                    )
                )
                del by_person[pid]
        return completed

    def active_snapshot(self) -> list[AnalyticsSessionRecord]:
        """Open sessions (exit_time unset)."""
        out: list[AnalyticsSessionRecord] = []
        now = utcnow()
        for by_person in self._active.values():
            for session in by_person.values():
                dwell = (now - session.entry_time).total_seconds()
                out.append(
                    AnalyticsSessionRecord(
                        person_id=session.person_id,
                        camera_id=session.camera_id,
                        entry_time=session.entry_time,
                        exit_time=None,
                        dwell_time=dwell,
                        zones=sorted(session.zones_visited),
                        zone_time=dict(session.zone_time),
                        interaction=session.interaction,
                        identity_type=session.identity_type,
                    )
                )
        return out
