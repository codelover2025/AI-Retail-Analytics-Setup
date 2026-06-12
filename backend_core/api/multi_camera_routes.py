"""Multi-camera analytics API (/api/footfall, dwell-time, zones, etc.)."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.schemas.multi_camera import (
    AIAnalyticsIngestBatch,
    AIAnalyticsIngestResponse,
    CameraListItem,
    DwellTimeStats,
    FootfallCameraResponse,
    InteractionsResponse,
    RepeatAnalyticsResponse,
    ZoneAnalyticsResponse,
    HeatmapResponse,
    JourneyResponse,
    JourneyStep,
    SessionOut,
    DemographicsResponse,
    MultiCameraSummaryResponse,
)
from backend_core.services.analytics import AnalyticsService
from backend_core.services.multi_camera_analytics import MultiCameraAnalyticsService
from shared.config import get_settings
from shared.database.session import get_db
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/api", tags=["multi-camera-analytics"])


def _svc(db: Session, tenant: TenantContext) -> MultiCameraAnalyticsService:
    return MultiCameraAnalyticsService(
        db, get_settings(), tenant.brand_id, tenant.store_external_id
    )


@router.get("/cameras", response_model=list[CameraListItem])
def list_cameras(
    store_id: Optional[str] = Query(default=None),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return _svc(db, tenant).list_cameras(store_id)


@router.post("/analytics-ingest", response_model=AIAnalyticsIngestResponse)
def ingest_ai_analytics(
    body: AIAnalyticsIngestBatch,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """Persist AI output batches (sessions, zones, interactions) without identity merge."""
    result = _svc(db, tenant).ingest_batch(body)
    db.commit()
    return result


@router.get("/footfall")
def get_footfall(
    camera_id: Optional[str] = Query(default=None),
    store_id: Optional[str] = Query(default=None),
    from_day: Optional[date] = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """
    Multi-camera footfall when `camera_id` or `store_id=ALL` is set.
    Legacy store footfall (daily + hourly) when neither is provided.
    """
    if camera_id or store_id == "ALL":
        return _svc(db, tenant).footfall(
            camera_id=camera_id,
            store_id=store_id or tenant.store_external_id,
            from_day=from_day,
            days=days,
        )
    legacy = AnalyticsService(db, get_settings(), tenant.brand_id)
    return legacy.footfall(
        store_id=store_id or tenant.store_external_id,
        from_day=from_day,
    )


@router.get("/dwell-time", response_model=DwellTimeStats)
def get_dwell_time(
    camera_id: Optional[str] = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return _svc(db, tenant).dwell_time(camera_id=camera_id, days=days)


@router.get("/zones", response_model=ZoneAnalyticsResponse)
def get_zones(
    camera_id: Optional[str] = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return _svc(db, tenant).zones(camera_id=camera_id, days=days)


@router.get("/repeat-analytics", response_model=RepeatAnalyticsResponse)
def get_repeat_analytics(
    camera_id: Optional[str] = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return _svc(db, tenant).repeat_analytics(camera_id=camera_id, days=days)


@router.get("/interactions", response_model=InteractionsResponse)
def get_interactions(
    camera_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return _svc(db, tenant).interactions(camera_id=camera_id, limit=limit)


@router.get("/heatmap", response_model=HeatmapResponse)
def get_heatmap(
    camera_id: Optional[str] = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return _svc(db, tenant).heatmap(camera_id=camera_id, days=days)


@router.get("/journey/{person_id}", response_model=JourneyResponse)
def get_journey(
    person_id: str,
    days: int = Query(default=30, ge=1, le=365),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return _svc(db, tenant).journey(person_id, days=days)


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(
    camera_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return _svc(db, tenant).list_sessions(camera_id=camera_id, limit=limit)


@router.get("/demographics", response_model=DemographicsResponse)
def get_demographics(
    days: int = Query(default=7, ge=1, le=90),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return _svc(db, tenant).demographics(days=days)


@router.get("/multi-camera/summary", response_model=MultiCameraSummaryResponse)
@router.get("/v1/analytics/multi-camera/summary", response_model=MultiCameraSummaryResponse)
def get_multi_camera_summary(
    camera_id: Optional[str] = Query(default=None),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    svc = _svc(db, tenant)
    cameras = svc.list_cameras()
    store_footfall = svc.footfall(store_id="ALL", camera_id=None, days=30)
    
    cam_param = None if camera_id == "ALL" or not camera_id else camera_id
    camera_footfall = svc.footfall(camera_id=cam_param, store_id=tenant.store_external_id, days=30) if cam_param else None
    dwell = svc.dwell_time(camera_id=cam_param, days=7)
    zones = svc.zones(camera_id=cam_param, days=7)
    repeat = svc.repeat_analytics(camera_id=cam_param, days=30)
    interactions = svc.interactions(camera_id=cam_param, limit=30)
    heatmap = svc.heatmap(camera_id=cam_param, days=7)
    
    return MultiCameraSummaryResponse(
        cameras=cameras,
        store_footfall=store_footfall,
        camera_footfall=camera_footfall,
        dwell=dwell,
        zones=zones,
        repeat=repeat,
        interactions=interactions,
        heatmap=heatmap,
    )
