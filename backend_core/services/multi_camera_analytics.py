"""Multi-camera analytics queries with optional TTL cache."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend_core.schemas.multi_camera import (
    AIAnalyticsIngestBatch,
    AIAnalyticsIngestResponse,
    CameraListItem,
    DwellTimeStats,
    FootfallCameraPoint,
    FootfallCameraResponse,
    InteractionItem,
    InteractionsResponse,
    RepeatAnalyticsResponse,
    ZoneAnalyticsItem,
    ZoneAnalyticsResponse,
)
from backend_core.services.analytics_aggregation import upsert_footfall_on_session
from shared.config import Settings
from shared.database.analytics_models import (
    AnalyticsSession,
    FootfallDailyCamera,
    Interaction,
    ZoneLog,
)
from shared.database.multi_camera_repository import MultiCameraAnalyticsRepository
from shared.database.tenant_models import Camera, Store


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class _TTLCache:
  def __init__(self, ttl_seconds: int = 60):
      self.ttl = ttl_seconds
      self._store: dict[str, tuple[float, Any]] = {}

  def get(self, key: str) -> Any | None:
      entry = self._store.get(key)
      if not entry:
          return None
      ts, value = entry
      if time.monotonic() - ts > self.ttl:
          del self._store[key]
          return None
      return value

  def set(self, key: str, value: Any) -> None:
      self._store[key] = (time.monotonic(), value)


_cache = _TTLCache(ttl_seconds=60)


def _cache_key(prefix: str, **kwargs: Any) -> str:
    raw = json.dumps(kwargs, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"


class MultiCameraAnalyticsService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        brand_id: uuid.UUID,
        default_store_id: str,
    ):
        self.db = db
        self.settings = settings
        self.brand_id = brand_id
        self.default_store_id = default_store_id
        self.repo = MultiCameraAnalyticsRepository(db, brand_id)

    def list_cameras(self, store_id: str | None = None) -> list[CameraListItem]:
        store_ext = store_id or self.default_store_id
        store = self.db.scalar(
            select(Store).where(
                Store.brand_id == self.brand_id,
                Store.external_id == store_ext,
            )
        )
        if store is None:
            return []
        cameras = self.db.scalars(
            select(Camera)
            .where(Camera.store_id == store.id)
            .order_by(Camera.external_id)
        ).all()
        return [
            CameraListItem(
                camera_id=c.external_id,
                name=c.name,
                enabled=c.enabled,
            )
            for c in cameras
        ]

    def ingest_batch(
        self, batch: AIAnalyticsIngestBatch, store_id: str | None = None
    ) -> AIAnalyticsIngestResponse:
        store_ext = batch.store_id or store_id or self.default_store_id
        sessions_n = 0
        zones_n = 0
        interactions_n = 0

        for s in batch.sessions:
            entry = s.entry_time or _utcnow()
            exit_t = s.exit_time
            prior = self.repo.count_sessions_for_person_camera(
                person_id=s.person_id,
                camera_id=s.camera_id,
                store_id=store_ext,
                before=entry,
            )
            self.repo.add_session(
                person_id=s.person_id,
                camera_id=s.camera_id,
                store_id=store_ext,
                entry_time=entry,
                exit_time=exit_t,
                dwell_time=s.dwell_time,
            )
            sessions_n += 1
            upsert_footfall_on_session(
                self.db,
                self.brand_id,
                store_id=store_ext,
                camera_id=s.camera_id,
                person_id=s.person_id,
                entry_time=entry,
                prior_visits=prior,
            )
            for z in s.zones:
                self.repo.add_zone_log(
                    person_id=s.person_id,
                    camera_id=s.camera_id,
                    store_id=store_ext,
                    zone_name=z.zone_name,
                    time_spent=z.time_spent,
                )
                zones_n += 1

        for ix in batch.interactions:
            ts = ix.timestamp or _utcnow()
            self.repo.add_interaction(
                customer_id=ix.customer_id,
                employee_id=ix.employee_id,
                camera_id=ix.camera_id,
                store_id=store_ext,
                timestamp=ts,
            )
            interactions_n += 1

        return AIAnalyticsIngestResponse(
            sessions_accepted=sessions_n,
            zone_logs_accepted=zones_n,
            interactions_accepted=interactions_n,
        )

    def footfall(
        self,
        *,
        camera_id: str | None = None,
        store_id: str | None = None,
        from_day: date | None = None,
        days: int = 30,
    ) -> FootfallCameraResponse:
        aggregated = store_id == "ALL"
        store_ext = self.default_store_id
        cache_key = _cache_key(
            "footfall",
            brand=str(self.brand_id),
            camera=camera_id,
            store=store_id,
            from_day=str(from_day),
            days=days,
        )
        cached = _cache.get(cache_key)
        if cached:
            return cached

        cutoff = from_day or (date.today() - timedelta(days=days))
        stmt = (
            select(FootfallDailyCamera)
            .where(
                FootfallDailyCamera.brand_id == self.brand_id,
                FootfallDailyCamera.day >= cutoff,
            )
            .order_by(FootfallDailyCamera.day.desc())
        )
        stmt = stmt.where(FootfallDailyCamera.store_id == store_ext)
        if camera_id:
            stmt = stmt.where(FootfallDailyCamera.camera_id == camera_id)

        rows = list(self.db.scalars(stmt).all())

        if aggregated and not camera_id:
            by_day: dict[date, tuple[int, int]] = {}
            for r in rows:
                t, rep = by_day.get(r.day, (0, 0))
                by_day[r.day] = (t + r.total_visitors, rep + r.repeat_visitors)
            points = [
                FootfallCameraPoint(
                    day=d,
                    camera_id=None,
                    total_visitors=t,
                    repeat_visitors=rep,
                    repeat_ratio=round(rep / t, 4) if t else 0.0,
                )
                for d, (t, rep) in sorted(by_day.items(), reverse=True)
            ]
        else:
            points = [
                FootfallCameraPoint(
                    day=r.day,
                    camera_id=r.camera_id if not camera_id else None,
                    total_visitors=r.total_visitors,
                    repeat_visitors=r.repeat_visitors,
                    repeat_ratio=(
                        round(r.repeat_visitors / r.total_visitors, 4)
                        if r.total_visitors
                        else 0.0
                    ),
                )
                for r in rows
            ]

        if points:
            total_v = sum(p.total_visitors for p in points)
            total_r = sum(p.repeat_visitors for p in points)
            summary = FootfallCameraPoint(
                day=points[0].day,
                camera_id=camera_id,
                total_visitors=total_v,
                repeat_visitors=total_r,
                repeat_ratio=round(total_r / total_v, 4) if total_v else 0.0,
            )
        else:
            summary = FootfallCameraPoint(
                day=date.today(),
                camera_id=camera_id,
                total_visitors=0,
                repeat_visitors=0,
                repeat_ratio=0.0,
            )

        resp = FootfallCameraResponse(
            store_id=store_ext,
            camera_id=camera_id,
            aggregated=aggregated,
            points=points,
            summary=summary,
        )
        _cache.set(cache_key, resp)
        return resp

    def dwell_time(self, *, camera_id: str | None = None, days: int = 7) -> DwellTimeStats:
        cache_key = _cache_key("dwell", brand=str(self.brand_id), camera=camera_id, days=days)
        cached = _cache.get(cache_key)
        if cached:
            return cached

        cutoff = _utcnow() - timedelta(days=days)
        stmt = select(AnalyticsSession.dwell_time).where(
            AnalyticsSession.brand_id == self.brand_id,
            AnalyticsSession.store_id == self.default_store_id,
            AnalyticsSession.entry_time >= cutoff,
        )
        if camera_id:
            stmt = stmt.where(AnalyticsSession.camera_id == camera_id)

        values = [float(v) for v in self.db.scalars(stmt).all()]
        if not values:
            resp = DwellTimeStats(
                camera_id=camera_id,
                session_count=0,
                avg_dwell_seconds=0.0,
                min_dwell_seconds=0.0,
                max_dwell_seconds=0.0,
                p50_dwell_seconds=0.0,
            )
        else:
            values.sort()
            n = len(values)
            p50 = values[n // 2]
            resp = DwellTimeStats(
                camera_id=camera_id,
                session_count=n,
                avg_dwell_seconds=round(sum(values) / n, 2),
                min_dwell_seconds=round(min(values), 2),
                max_dwell_seconds=round(max(values), 2),
                p50_dwell_seconds=round(p50, 2),
            )
        _cache.set(cache_key, resp)
        return resp

    def zones(self, *, camera_id: str | None = None, days: int = 7) -> ZoneAnalyticsResponse:
        cache_key = _cache_key("zones", brand=str(self.brand_id), camera=camera_id, days=days)
        cached = _cache.get(cache_key)
        if cached:
            return cached

        stmt = (
            select(
                ZoneLog.zone_name,
                func.sum(ZoneLog.time_spent).label("total_time"),
                func.count().label("visits"),
            )
            .where(
                ZoneLog.brand_id == self.brand_id,
                ZoneLog.store_id == self.default_store_id,
            )
            .group_by(ZoneLog.zone_name)
            .order_by(func.sum(ZoneLog.time_spent).desc())
        )
        if camera_id:
            stmt = stmt.where(ZoneLog.camera_id == camera_id)
        # Filter by time via join to sessions is heavy; zone logs are append-only per ingest
        rows = self.db.execute(stmt).all()
        zones = [
            ZoneAnalyticsItem(
                zone_name=r.zone_name,
                total_time_spent=round(float(r.total_time or 0), 2),
                visit_count=int(r.visits or 0),
                avg_time_spent=round(float(r.total_time or 0) / max(int(r.visits or 1), 1), 2),
            )
            for r in rows
        ]
        resp = ZoneAnalyticsResponse(camera_id=camera_id, zones=zones)
        _cache.set(cache_key, resp)
        return resp

    def repeat_analytics(
        self, *, camera_id: str | None = None, days: int = 30
    ) -> RepeatAnalyticsResponse:
        footfall = self.footfall(camera_id=camera_id, days=days)
        total = footfall.summary.total_visitors
        repeat = footfall.summary.repeat_visitors
        return RepeatAnalyticsResponse(
            camera_id=camera_id,
            total_visitors=total,
            repeat_visitors=repeat,
            new_visitors=max(total - repeat, 0),
            repeat_ratio=footfall.summary.repeat_ratio,
        )

    def interactions(
        self, *, camera_id: str | None = None, limit: int = 100
    ) -> InteractionsResponse:
        stmt = (
            select(Interaction)
            .where(
                Interaction.brand_id == self.brand_id,
                Interaction.store_id == self.default_store_id,
            )
            .order_by(Interaction.timestamp.desc())
            .limit(limit)
        )
        if camera_id:
            stmt = stmt.where(Interaction.camera_id == camera_id)
        rows = list(self.db.scalars(stmt).all())
        items = [
            InteractionItem(
                id=str(r.id),
                customer_id=r.customer_id,
                employee_id=r.employee_id,
                camera_id=r.camera_id,
                timestamp=r.timestamp,
            )
            for r in rows
        ]
        return InteractionsResponse(camera_id=camera_id, total=len(items), items=items)
