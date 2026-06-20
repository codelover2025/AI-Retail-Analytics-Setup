"""Predictive Analytics & Forecasting API routes (Phase 5)."""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.auth.rbac import UserContext, require_role
from backend_core.services.ai.predictive_analytics import PredictiveAnalyticsService
from backend_core.services.ai.forecasting_engine import ForecastingEngine
from shared.database.session import get_db
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/api/v1/ai", tags=["ai-analytics"])


@router.get("/predictions", summary="Get predictive analytics for a store")
def get_predictions(
    store_id: Optional[str] = Query(default=None, description="Store external ID; defaults to active store"),
    days_ahead: int = Query(default=7, ge=1, le=30),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """
    Returns store predictions based on historical trends:
    - Footfall prediction
    - Peak hour predictions
    - Repeat visitor prediction
    - Conversion probability
    - Staff requirement prediction
    - Store performance index
    """
    sid = store_id or tenant.store_external_id
    svc = PredictiveAnalyticsService(db, tenant.brand_id)
    
    footfall = svc.predict_footfall(sid, days_ahead=days_ahead)
    peak_hours = svc.predict_peak_hours(sid)
    repeats = svc.predict_repeat_visitors(sid, days_ahead=days_ahead)
    conversion = svc.predict_conversion_probability(sid, days_ahead=days_ahead)
    staffing = svc.predict_staff_requirement(sid, days_ahead=days_ahead)
    performance = svc.predict_store_performance(sid)

    return {
        "store_id": sid,
        "days_ahead": days_ahead,
        "predictions": {
            "footfall": footfall,
            "peak_hours": peak_hours,
            "repeat_visitors": repeats,
            "conversion_probability": conversion,
            "staff_requirements": staffing,
            "store_performance": performance
        }
    }


@router.get("/forecasts", summary="Get daily/weekly/monthly forecasts with confidence intervals")
def get_forecasts(
    store_id: Optional[str] = Query(default=None, description="Store external ID"),
    horizon: str = Query(default="daily", description="Forecast horizon: daily (7 days), weekly (4 weeks), or monthly (3 months)"),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """
    Returns statistical forecasts with 95% confidence intervals:
    - Revenue forecast
    - Store growth forecast (footfall percentage)
    - Retention forecast (repeat visitor counts)
    """
    sid = store_id or tenant.store_external_id
    engine = ForecastingEngine(db, tenant.brand_id)
    
    revenue = engine.forecast_revenue(sid, horizon=horizon)
    growth = engine.forecast_growth(sid, horizon=horizon)
    retention = engine.forecast_retention(sid, horizon=horizon)

    return {
        "store_id": sid,
        "horizon": horizon,
        "forecasts": {
            "revenue": revenue,
            "growth": growth,
            "retention": retention
        }
    }
