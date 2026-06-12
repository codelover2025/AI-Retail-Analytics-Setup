"""
Dashboard API routes — Module 1 (Phase 4).

Endpoints:
  GET /api/dashboard/overview    - brand-level aggregate
  GET /api/dashboard/stores      - per-store paginated list
  GET /api/dashboard/comparison  - side-by-side store comparison
  GET /api/dashboard/cameras     - camera-level breakdown for a store
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.auth.rbac import UserContext, require_role
from backend_core.services.dashboard_service import DashboardService
from shared.config import get_settings
from shared.database.session import get_db
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _svc(db: Session, tenant: TenantContext) -> DashboardService:
    return DashboardService(db, get_settings(), tenant.brand_id)


@router.get("/overview", summary="Brand-level analytics overview")
def overview(
    from_day: Optional[date] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    to_day: Optional[date] = Query(default=None, description="End date (YYYY-MM-DD)"),
    store_ids: Optional[str] = Query(
        default=None,
        description="Comma-separated store external IDs to filter; omit for all stores",
    ),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """
    Aggregate visitor metrics across all stores for the authenticated brand.

    Supports optional date range and store filter.  Results are cached
    server-side for `DASHBOARD_CACHE_TTL_SECONDS` seconds (default 300).
    """
    store_list = [s.strip() for s in store_ids.split(",")] if store_ids else None
    return _svc(db, tenant).overview(
        from_day=from_day,
        to_day=to_day,
        store_ids=store_list,
    )


@router.get("/stores", summary="Per-store metrics list (paginated)")
def stores_list(
    from_day: Optional[date] = Query(default=None),
    to_day: Optional[date] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="total_visitors"),
    sort_desc: bool = Query(default=True),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """
    Returns paginated list of stores with their analytics metrics.

    `sort_by` can be one of: `total_visitors`, `repeat_visitors`,
    `avg_dwell_seconds`, `staff_interactions`, `repeat_ratio`.
    """
    return _svc(db, tenant).stores_list(
        from_day=from_day,
        to_day=to_day,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )


@router.get("/comparison", summary="Side-by-side store comparison")
def comparison(
    store_ids: str = Query(
        ...,
        description="Comma-separated store external IDs (2–10 stores)",
    ),
    from_day: Optional[date] = Query(default=None),
    to_day: Optional[date] = Query(default=None),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """
    Returns side-by-side comparison metrics for selected stores, ranked
    by total visitors with a vs-best percentage delta.
    """
    ids = [s.strip() for s in store_ids.split(",") if s.strip()]
    return _svc(db, tenant).comparison(ids, from_day=from_day, to_day=to_day)


@router.get("/cameras", summary="Camera-level breakdown for a store")
def camera_breakdown(
    store_id: Optional[str] = Query(default=None),
    from_day: Optional[date] = Query(default=None),
    to_day: Optional[date] = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """Per-camera footfall, dwell, and zone data for one store."""
    sid = store_id or tenant.store_external_id
    return _svc(db, tenant).camera_breakdown(
        sid, from_day=from_day, to_day=to_day, days=days
    )
