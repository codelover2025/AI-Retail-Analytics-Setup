from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend_core.auth import verify_api_key
from backend_core.schemas.contract import (
    AlertItem,
    FootfallResponse,
    LiveVisitorsResponse,
    RecognitionItem,
)
from backend_core.services.analytics import AnalyticsService
from shared.database.session import get_db


def _settings():
    from shared.config import get_settings

    return get_settings()


router = APIRouter(prefix="/api", dependencies=[Depends(verify_api_key)])


@router.get("/live-visitors", response_model=LiveVisitorsResponse)
def get_live_visitors(
    store_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db, _settings())
    return svc.live_visitors(store_id)


@router.get("/recognitions", response_model=list[RecognitionItem])
def get_recognitions(
    store_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db, _settings())
    return svc.recognitions(store_id=store_id, limit=limit)


@router.get("/footfall", response_model=FootfallResponse)
def get_footfall(
    store_id: Optional[str] = Query(default=None),
    from_day: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db, _settings())
    return svc.footfall(store_id=store_id, from_day=from_day)


@router.get("/alerts", response_model=list[AlertItem])
def get_alerts(
    store_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    unacknowledged_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db, _settings())
    return svc.alerts(
        store_id=store_id,
        limit=limit,
        unacknowledged_only=unacknowledged_only,
    )
