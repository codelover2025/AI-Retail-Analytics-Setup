"""
Heatmap API — Module 4 (Phase 4).

Endpoints:
  GET /api/heatmap/zone        — zone dwell-density heatmap data
  GET /api/heatmap/occupancy   — zone visit-frequency heatmap
  GET /api/heatmap/dwell       — avg dwell-weighted heatmap
  GET /api/heatmap/hourly      — hourly session distribution (0-23h)
  GET /api/heatmap/multi-store — brand-level cross-store heatmap
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.auth.rbac import UserContext, require_role
from backend_core.services.heatmap_service import HeatmapService
from shared.config import get_settings
from shared.database.session import get_db
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/api/heatmap", tags=["heatmap"])


def _svc(db: Session, tenant: TenantContext, store_id: Optional[str] = None) -> HeatmapService:
    sid = store_id or tenant.store_external_id
    return HeatmapService(db, get_settings(), tenant.brand_id, sid)


@router.get("/zone", summary="Zone dwell-density heatmap data")
def zone_heatmap(
    store_id: Optional[str] = Query(default=None),
    camera_id: Optional[str] = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """
    Returns per-zone intensity values weighted by total dwell time.

    Intensity is normalized to [0.0, 1.0] where 1.0 = highest dwell zone.
    """
    return _svc(db, tenant, store_id).zone_density(camera_id=camera_id, days=days)


@router.get("/occupancy", summary="Zone occupancy (visit frequency) heatmap")
def occupancy_heatmap(
    store_id: Optional[str] = Query(default=None),
    camera_id: Optional[str] = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """Intensity weighted by visit count — shows highest traffic zones."""
    return _svc(db, tenant, store_id).zone_occupancy(camera_id=camera_id, days=days)


@router.get("/dwell", summary="Average dwell-weighted zone heatmap")
def dwell_heatmap(
    store_id: Optional[str] = Query(default=None),
    camera_id: Optional[str] = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """Intensity = average dwell per visit; shows zones where visitors linger."""
    return _svc(db, tenant, store_id).dwell_heatmap(camera_id=camera_id, days=days)


@router.get("/hourly", summary="Hourly visitor distribution heatmap (0–23h)")
def hourly_heatmap(
    store_id: Optional[str] = Query(default=None),
    camera_id: Optional[str] = Query(default=None),
    zone_name: Optional[str] = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """
    Returns 24 hourly buckets with normalized intensity.

    Use for store opening hours analysis and peak hour detection.
    """
    return _svc(db, tenant, store_id).hourly_heatmap(
        camera_id=camera_id, days=days, zone_name=zone_name
    )


@router.get("/multi-store", summary="Brand-level multi-store heatmap")
def multi_store_heatmap(
    store_ids: Optional[str] = Query(
        default=None,
        description="Comma-separated store IDs; omit for all brand stores",
    ),
    days: int = Query(default=7, ge=1, le=90),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """
    Aggregates zone heatmap data across all (or selected) stores.

    Returns per-store zone intensity for multi-store floor plan rendering.
    """
    ids = [s.strip() for s in store_ids.split(",")] if store_ids else None
    svc = HeatmapService(db, get_settings(), tenant.brand_id, tenant.store_external_id)
    return svc.multi_store_heatmap(store_ids=ids, days=days)
