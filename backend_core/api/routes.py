from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend_core.auth import verify_api_key
from shared.database.models import Visitor
from shared.database.repository import AnalyticsRepository
from shared.database.session import get_db
from shared.schemas import AlertOut, FootfallOut, LiveVisitorOut, RecognitionOut, VisitorOut

router = APIRouter(prefix="/api", dependencies=[Depends(verify_api_key)])


@router.get("/live-visitors", response_model=list[LiveVisitorOut])
def get_live_visitors(
    store_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    repo = AnalyticsRepository(db, _settings())
    rows = repo.get_live_visitors(store_id=store_id)
    out: list[LiveVisitorOut] = []
    for row in rows:
        visitor = None
        if row.visitor_id:
            v = db.get(Visitor, row.visitor_id)
            if v:
                visitor = VisitorOut.model_validate(v)
        out.append(
            LiveVisitorOut(
                track_id=row.track_id,
                visitor_id=row.visitor_id,
                store_id=row.store_id,
                camera_id=row.camera_id,
                bbox=row.bbox,
                confidence=row.confidence,
                last_seen_at=row.last_seen_at,
                visitor=visitor,
            )
        )
    return out


@router.get("/recognitions", response_model=list[RecognitionOut])
def get_recognitions(
    store_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    repo = AnalyticsRepository(db, _settings())
    return repo.get_recognitions(store_id=store_id, limit=limit)


@router.get("/footfall", response_model=list[FootfallOut])
def get_footfall(
    store_id: Optional[str] = Query(default=None),
    from_day: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    repo = AnalyticsRepository(db, _settings())
    return repo.get_footfall(store_id=store_id, from_day=from_day)


@router.get("/alerts", response_model=list[AlertOut])
def get_alerts(
    store_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    unacknowledged_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    repo = AnalyticsRepository(db, _settings())
    return repo.get_alerts(
        store_id=store_id,
        limit=limit,
        unacknowledged_only=unacknowledged_only,
    )


def _settings():
    from shared.config import get_settings

    return get_settings()
