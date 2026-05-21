from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.schemas.contract import (
    AlertItem,
    FootfallResponse,
    LiveVisitorsResponse,
    RecognitionItem,
)
from backend_core.services.analytics import AnalyticsService
from shared.config import get_settings
from shared.database.session import get_db
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/live-visitors", response_model=LiveVisitorsResponse)
def get_live_visitors(
    store_id: Optional[str] = Query(default=None),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db, get_settings(), tenant.brand_id)
    return svc.live_visitors(store_id or tenant.store_external_id)


@router.get("/recognitions", response_model=list[RecognitionItem])
def get_recognitions(
    store_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db, get_settings(), tenant.brand_id)
    return svc.recognitions(store_id=store_id or tenant.store_external_id, limit=limit)


@router.get("/footfall", response_model=FootfallResponse)
def get_footfall(
    store_id: Optional[str] = Query(default=None),
    from_day: Optional[date] = Query(default=None),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db, get_settings(), tenant.brand_id)
    return svc.footfall(store_id=store_id or tenant.store_external_id, from_day=from_day)


@router.get("/alerts", response_model=list[AlertItem])
def get_alerts(
    store_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    unacknowledged_only: bool = Query(default=False),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db, get_settings(), tenant.brand_id)
    return svc.alerts(
        store_id=store_id or tenant.store_external_id,
        limit=limit,
        unacknowledged_only=unacknowledged_only,
    )
