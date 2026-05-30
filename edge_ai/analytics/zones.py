"""Zone polygons — centroid assignment per camera."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZonePolygon:
    name: str
    points: list[tuple[float, float]]


@dataclass(frozen=True)
class CameraZones:
    camera_id: str
    zones: tuple[ZonePolygon, ...]


def bbox_centroid(bbox: list[float]) -> tuple[float, float]:
    x1, y1, x2, y2 = bbox[:4]
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def point_in_polygon(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon (stable for convex/concave retail zones)."""
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi
        ):
            inside = not inside
        j = i
    return inside


def zones_for_centroid(
    centroid: tuple[float, float], camera_zones: CameraZones
) -> list[str]:
    x, y = centroid
    hits: list[str] = []
    for zone in camera_zones.zones:
        if point_in_polygon(x, y, zone.points):
            hits.append(zone.name)
    return hits


def _parse_zone_points(raw: Any) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for pt in raw:
        if isinstance(pt, (list, tuple)) and len(pt) >= 2:
            points.append((float(pt[0]), float(pt[1])))
    return points


def load_zones_from_json(raw: str | dict) -> dict[str, CameraZones]:
    data = json.loads(raw) if isinstance(raw, str) else raw
    out: dict[str, CameraZones] = {}
    for camera_id, zone_map in data.items():
        polys: list[ZonePolygon] = []
        if isinstance(zone_map, dict):
            for name, points in zone_map.items():
                pts = _parse_zone_points(points)
                if len(pts) >= 3:
                    polys.append(ZonePolygon(name=name, points=pts))
        out[str(camera_id)] = CameraZones(camera_id=str(camera_id), zones=tuple(polys))
    return out


def load_zones(settings) -> dict[str, CameraZones]:
    """Load from ZONES_JSON env or optional zones.json in project root."""
    if settings.zones_json:
        return load_zones_from_json(settings.zones_json)
    path = Path("zones.json")
    if path.is_file():
        return load_zones_from_json(path.read_text(encoding="utf-8"))
    return {}
