"""
Dashboard aggregation service — Module 1 (Phase 4).

Aggregates footfall, dwell, zones, and staff interactions across
multiple stores and cameras for brand-level and per-store dashboards.
Reuses MultiCameraAnalyticsService per store — no duplicate logic.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend_core.services.multi_camera_analytics import MultiCameraAnalyticsService
from shared.cache.redis_cache import RedisCache, make_cache_key
from shared.config import Settings
from shared.database.analytics_models import AnalyticsSession, FootfallDailyCamera, Interaction, ZoneLog
from shared.database.tenant_models import Store
from shared.schemas.pagination import paginate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DashboardService:
    """
    Brand-level and store-level analytics aggregation.

    Instantiated per request — lightweight; shares the same DB session.
    """

    def __init__(
        self,
        db: Session,
        settings: Settings,
        brand_id: uuid.UUID,
        cache: Optional[RedisCache] = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.brand_id = brand_id
        self._cache = cache or RedisCache(
            redis_url=settings.redis_url,
            default_ttl=settings.dashboard_cache_ttl_seconds,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _list_active_stores(self) -> list[Store]:
        return list(
            self.db.scalars(
                select(Store)
                .where(Store.brand_id == self.brand_id, Store.is_active == True)
                .order_by(Store.name)
            ).all()
        )

    def _store_svc(self, store: Store) -> MultiCameraAnalyticsService:
        return MultiCameraAnalyticsService(
            self.db, self.settings, self.brand_id, store.external_id
        )

    def _footfall_for_store(
        self,
        store_ext: str,
        from_day: date,
        to_day: date,
    ) -> dict[str, Any]:
        days = (to_day - from_day).days + 1
        svc = MultiCameraAnalyticsService(
            self.db, self.settings, self.brand_id, store_ext
        )
        ff = svc.footfall(store_id="ALL", days=days, from_day=from_day)
        dwell = svc.dwell_time(days=days)
        zones = svc.zones(days=days)
        interactions = svc.interactions(limit=1)  # only count matters
        repeat = svc.repeat_analytics(days=days)

        top_zone = zones.zones[0].zone_name if zones.zones else None

        return {
            "store_id": store_ext,
            "total_visitors": ff.summary.total_visitors,
            "repeat_visitors": ff.summary.repeat_visitors,
            "new_visitors": repeat.new_visitors,
            "repeat_ratio": ff.summary.repeat_ratio,
            "avg_dwell_seconds": dwell.avg_dwell_seconds,
            "staff_interactions": interactions.total,
            "top_zone": top_zone,
            "zone_count": len(zones.zones),
        }

    # ------------------------------------------------------------------
    # /api/dashboard/overview
    # ------------------------------------------------------------------

    def overview(
        self,
        *,
        from_day: Optional[date] = None,
        to_day: Optional[date] = None,
        store_ids: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Brand-level aggregate across all (or selected) stores."""
        to_day = to_day or date.today()
        from_day = from_day or (to_day - timedelta(days=29))

        key = make_cache_key(
            "dash:overview",
            brand=str(self.brand_id),
            from_day=str(from_day),
            to_day=str(to_day),
            stores=sorted(store_ids or []),
        )

        # Sync cache check (no async in sync FastAPI route)
        cached = self._cache._local.get(key)
        if cached is not None:
            return cached

        stores = self._list_active_stores()
        if store_ids:
            stores = [s for s in stores if s.external_id in store_ids]

        brand_totals: dict[str, Any] = {
            "total_visitors": 0,
            "repeat_visitors": 0,
            "new_visitors": 0,
            "avg_dwell_seconds": 0.0,
            "staff_interactions": 0,
            "store_count": len(stores),
        }

        store_metrics = []
        dwell_sum = 0.0
        dwell_stores = 0

        for store in stores:
            m = self._footfall_for_store(store.external_id, from_day, to_day)
            store_metrics.append(m)
            brand_totals["total_visitors"] += m["total_visitors"]
            brand_totals["repeat_visitors"] += m["repeat_visitors"]
            brand_totals["new_visitors"] += m["new_visitors"]
            brand_totals["staff_interactions"] += m["staff_interactions"]
            if m["avg_dwell_seconds"] > 0:
                dwell_sum += m["avg_dwell_seconds"]
                dwell_stores += 1

        brand_totals["avg_dwell_seconds"] = round(
            dwell_sum / dwell_stores if dwell_stores else 0.0, 2
        )
        total = brand_totals["total_visitors"]
        brand_totals["repeat_ratio"] = round(
            brand_totals["repeat_visitors"] / total if total else 0.0, 4
        )

        result = {
            "brand_id": str(self.brand_id),
            "from_day": str(from_day),
            "to_day": str(to_day),
            "summary": brand_totals,
            "stores": store_metrics,
            "generated_at": _utcnow().isoformat(),
        }

        self._cache._local.set(key, result)
        return result

    # ------------------------------------------------------------------
    # /api/dashboard/stores
    # ------------------------------------------------------------------

    def stores_list(
        self,
        *,
        from_day: Optional[date] = None,
        to_day: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "total_visitors",
        sort_desc: bool = True,
    ) -> dict[str, Any]:
        """Per-store metrics list with pagination and sorting."""
        to_day = to_day or date.today()
        from_day = from_day or (to_day - timedelta(days=29))

        stores = self._list_active_stores()
        total = len(stores)

        all_metrics = [
            self._footfall_for_store(s.external_id, from_day, to_day)
            for s in stores
        ]

        # Sorting
        valid_sorts = {
            "total_visitors", "repeat_visitors", "avg_dwell_seconds",
            "staff_interactions", "repeat_ratio",
        }
        sort_field = sort_by if sort_by in valid_sorts else "total_visitors"
        all_metrics.sort(
            key=lambda x: x.get(sort_field, 0),
            reverse=sort_desc,
        )

        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        page_items = all_metrics[start:end]

        return paginate(page_items, total=total, page=page, page_size=page_size)

    # ------------------------------------------------------------------
    # /api/dashboard/comparison
    # ------------------------------------------------------------------

    def comparison(
        self,
        store_ids: list[str],
        *,
        from_day: Optional[date] = None,
        to_day: Optional[date] = None,
    ) -> dict[str, Any]:
        """Side-by-side metric comparison for selected stores."""
        to_day = to_day or date.today()
        from_day = from_day or (to_day - timedelta(days=29))
        store_ids = store_ids[: self.settings.max_store_comparison]

        metrics = [
            self._footfall_for_store(sid, from_day, to_day)
            for sid in store_ids
        ]

        # Rank by total visitors
        ranked = sorted(metrics, key=lambda x: x["total_visitors"], reverse=True)
        for i, m in enumerate(ranked):
            m["rank"] = i + 1

        # Compute deltas vs best-performing store
        best_visitors = ranked[0]["total_visitors"] if ranked else 1
        for m in ranked:
            m["vs_best_pct"] = round(
                (m["total_visitors"] / best_visitors - 1) * 100 if best_visitors else 0,
                1,
            )

        return {
            "from_day": str(from_day),
            "to_day": str(to_day),
            "stores": ranked,
            "generated_at": _utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # Camera-level drill-down
    # ------------------------------------------------------------------

    def camera_breakdown(
        self,
        store_id: str,
        *,
        from_day: Optional[date] = None,
        to_day: Optional[date] = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """Per-camera breakdown for a single store."""
        to_day = to_day or date.today()
        from_day = from_day or (to_day - timedelta(days=days - 1))
        svc = MultiCameraAnalyticsService(
            self.db, self.settings, self.brand_id, store_id
        )
        cameras = svc.list_cameras(store_id)
        camera_data = []
        for cam in cameras:
            ff = svc.footfall(camera_id=cam.camera_id, from_day=from_day, days=days)
            dw = svc.dwell_time(camera_id=cam.camera_id, days=days)
            zm = svc.zones(camera_id=cam.camera_id, days=days)
            camera_data.append({
                "camera_id": cam.camera_id,
                "name": cam.name,
                "enabled": cam.enabled,
                "total_visitors": ff.summary.total_visitors,
                "repeat_visitors": ff.summary.repeat_visitors,
                "avg_dwell_seconds": dw.avg_dwell_seconds,
                "top_zone": zm.zones[0].zone_name if zm.zones else None,
            })
        return {
            "store_id": store_id,
            "from_day": str(from_day),
            "to_day": str(to_day),
            "cameras": camera_data,
        }
