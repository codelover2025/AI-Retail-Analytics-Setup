"""
Heatmap service — Module 4 (Phase 4).

Generates optimized heatmap data (coordinate datasets + intensity layers).
No image generation — pure data output for frontend rendering.
Extends existing MultiCameraAnalyticsService zone data.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.config import Settings
from shared.database.analytics_models import ZoneLog, AnalyticsSession


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HeatmapService:
    """
    Produces heatmap data layers from zone logs and analytics sessions.

    All outputs are normalized intensity values in [0.0, 1.0].
    """

    def __init__(
        self,
        db: Session,
        settings: Settings,
        brand_id: uuid.UUID,
        store_id: str,
    ) -> None:
        self.db = db
        self.settings = settings
        self.brand_id = brand_id
        self.store_id = store_id

    # ------------------------------------------------------------------
    # Zone density heatmap
    # ------------------------------------------------------------------

    def zone_density(
        self,
        *,
        camera_id: Optional[str] = None,
        days: int = 7,
    ) -> dict:
        """Normalized dwell-time density per zone."""
        cutoff = _utcnow() - timedelta(days=days)
        stmt = (
            select(
                ZoneLog.zone_name,
                func.sum(ZoneLog.time_spent).label("total_time"),
                func.count().label("visit_count"),
            )
            .where(
                ZoneLog.brand_id == self.brand_id,
                ZoneLog.store_id == self.store_id,
            )
            .group_by(ZoneLog.zone_name)
            .order_by(func.sum(ZoneLog.time_spent).desc())
        )
        if camera_id:
            stmt = stmt.where(ZoneLog.camera_id == camera_id)

        rows = self.db.execute(stmt).all()
        if not rows:
            return {"camera_id": camera_id, "store_id": self.store_id, "cells": [], "type": "zone_density"}

        max_time = max(float(r.total_time or 0) for r in rows) or 1.0
        cells = [
            {
                "zone_name": r.zone_name,
                "intensity": round(float(r.total_time or 0) / max_time, 4),
                "total_time_spent": round(float(r.total_time or 0), 2),
                "visit_count": int(r.visit_count or 0),
                "avg_time_spent": round(float(r.total_time or 0) / max(int(r.visit_count or 1), 1), 2),
            }
            for r in rows
        ]
        return {
            "camera_id": camera_id,
            "store_id": self.store_id,
            "days": days,
            "type": "zone_density",
            "cells": cells,
        }

    # ------------------------------------------------------------------
    # Zone occupancy heatmap
    # ------------------------------------------------------------------

    def zone_occupancy(
        self,
        *,
        camera_id: Optional[str] = None,
        days: int = 7,
    ) -> dict:
        """Normalized visit count (occupancy frequency) per zone."""
        stmt = (
            select(
                ZoneLog.zone_name,
                func.count().label("visit_count"),
                func.sum(ZoneLog.time_spent).label("total_time"),
            )
            .where(
                ZoneLog.brand_id == self.brand_id,
                ZoneLog.store_id == self.store_id,
            )
            .group_by(ZoneLog.zone_name)
            .order_by(func.count().desc())
        )
        if camera_id:
            stmt = stmt.where(ZoneLog.camera_id == camera_id)

        rows = self.db.execute(stmt).all()
        if not rows:
            return {"camera_id": camera_id, "store_id": self.store_id, "cells": [], "type": "zone_occupancy"}

        max_visits = max(int(r.visit_count or 0) for r in rows) or 1
        cells = [
            {
                "zone_name": r.zone_name,
                "intensity": round(int(r.visit_count or 0) / max_visits, 4),
                "visit_count": int(r.visit_count or 0),
                "total_time_spent": round(float(r.total_time or 0), 2),
            }
            for r in rows
        ]
        return {
            "camera_id": camera_id,
            "store_id": self.store_id,
            "days": days,
            "type": "zone_occupancy",
            "cells": cells,
        }

    # ------------------------------------------------------------------
    # Dwell-weighted heatmap
    # ------------------------------------------------------------------

    def dwell_heatmap(
        self,
        *,
        camera_id: Optional[str] = None,
        days: int = 7,
    ) -> dict:
        """
        Returns zone cells weighted by average dwell time.
        High intensity = zones where visitors stay longest on average.
        """
        stmt = (
            select(
                ZoneLog.zone_name,
                func.avg(ZoneLog.time_spent).label("avg_dwell"),
                func.count().label("visit_count"),
            )
            .where(
                ZoneLog.brand_id == self.brand_id,
                ZoneLog.store_id == self.store_id,
            )
            .group_by(ZoneLog.zone_name)
            .order_by(func.avg(ZoneLog.time_spent).desc())
        )
        if camera_id:
            stmt = stmt.where(ZoneLog.camera_id == camera_id)

        rows = self.db.execute(stmt).all()
        if not rows:
            return {"camera_id": camera_id, "store_id": self.store_id, "cells": [], "type": "dwell_heatmap"}

        max_dwell = max(float(r.avg_dwell or 0) for r in rows) or 1.0
        cells = [
            {
                "zone_name": r.zone_name,
                "intensity": round(float(r.avg_dwell or 0) / max_dwell, 4),
                "avg_dwell_seconds": round(float(r.avg_dwell or 0), 2),
                "visit_count": int(r.visit_count or 0),
            }
            for r in rows
        ]
        return {
            "camera_id": camera_id,
            "store_id": self.store_id,
            "days": days,
            "type": "dwell_heatmap",
            "cells": cells,
        }

    # ------------------------------------------------------------------
    # Hourly heatmap
    # ------------------------------------------------------------------

    def hourly_heatmap(
        self,
        *,
        camera_id: Optional[str] = None,
        days: int = 7,
        zone_name: Optional[str] = None,
    ) -> dict:
        """
        Hourly visit distribution — intensity per hour bucket (0–23).
        Optionally filtered by zone_name.
        """
        from shared.database.session import is_sqlite

        cutoff = _utcnow() - timedelta(days=days)

        if is_sqlite():
            hour_expr = func.strftime("%H", ZoneLog.created_at).label("hour")
        else:
            # Use analytics_sessions entry_time for hour distribution
            hour_expr = func.extract("hour", AnalyticsSession.entry_time).label("hour")

        # Build hourly from analytics_sessions (more reliable than zone_log timestamps)
        stmt = (
            select(
                func.extract("hour", AnalyticsSession.entry_time).label("hour"),
                func.count().label("session_count"),
            )
            .where(
                AnalyticsSession.brand_id == self.brand_id,
                AnalyticsSession.store_id == self.store_id,
                AnalyticsSession.entry_time >= cutoff,
            )
            .group_by(func.extract("hour", AnalyticsSession.entry_time))
            .order_by(func.extract("hour", AnalyticsSession.entry_time))
        )
        if camera_id:
            stmt = stmt.where(AnalyticsSession.camera_id == camera_id)

        rows = self.db.execute(stmt).all()

        # Build full 24-hour array
        hour_map = {int(r.hour): int(r.session_count) for r in rows}
        max_count = max(hour_map.values()) if hour_map else 1

        buckets = [
            {
                "hour": h,
                "session_count": hour_map.get(h, 0),
                "intensity": round(hour_map.get(h, 0) / max_count, 4),
            }
            for h in range(24)
        ]

        return {
            "camera_id": camera_id,
            "store_id": self.store_id,
            "zone_name": zone_name,
            "days": days,
            "type": "hourly_heatmap",
            "buckets": buckets,
        }

    # ------------------------------------------------------------------
    # Multi-store brand-level heatmap
    # ------------------------------------------------------------------

    def multi_store_heatmap(
        self,
        store_ids: Optional[list[str]] = None,
        *,
        days: int = 7,
    ) -> dict:
        """
        Aggregates zone intensity across multiple stores at brand level.
        Returns per-store zone density for frontend multi-store layout.
        """
        from sqlalchemy import distinct
        from shared.database.tenant_models import Store

        stores = self.db.scalars(
            select(Store).where(
                Store.brand_id == self.brand_id,
                Store.is_active == True,
            )
        ).all()

        if store_ids:
            stores = [s for s in stores if s.external_id in store_ids]

        result = []
        for store in stores:
            svc = HeatmapService(self.db, self.settings, self.brand_id, store.external_id)
            density = svc.zone_density(days=days)
            result.append({
                "store_id": store.external_id,
                "store_name": store.name,
                "cells": density.get("cells", []),
            })

        return {
            "brand_id": str(self.brand_id),
            "days": days,
            "type": "multi_store_heatmap",
            "stores": result,
        }
