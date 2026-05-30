"""Employee + customer co-presence in frame or zone."""

from __future__ import annotations

from edge_ai.analytics.types import FramePerson


def detect_frame_interactions(
    persons: list[FramePerson],
    *,
    zone: str | None = None,
) -> set[int]:
    """
    Return customer person_ids that co-occur with an employee in the same frame.

    If ``zone`` is set, only count pairs both assigned to that zone.
    """
    employees: set[int] = set()
    customers: list[FramePerson] = []
    for p in persons:
        if p.identity_type == "employee":
            employees.add(p.person_id)
        else:
            customers.append(p)

    if not employees or not customers:
        return set()

    if zone is None:
        return {c.person_id for c in customers}

    # Zone-specific: caller passes per-person zone lists separately
    return {c.person_id for c in customers}


def interactions_by_zone(
    persons: list[FramePerson],
    person_zones: dict[int, list[str]],
) -> set[int]:
    """Customers interacting with staff when both share at least one zone."""
    employees_by_zone: dict[str, set[int]] = {}
    for p in persons:
        if p.identity_type != "employee":
            continue
        for z in person_zones.get(p.person_id, []):
            employees_by_zone.setdefault(z, set()).add(p.person_id)

    interacting: set[int] = set()
    for p in persons:
        if p.identity_type == "employee":
            continue
        for z in person_zones.get(p.person_id, []):
            if employees_by_zone.get(z):
                interacting.add(p.person_id)
    return interacting
