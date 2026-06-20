"""Recommendation & AI Alerts API routes (Phase 5)."""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.auth.rbac import UserContext, require_role
from backend_core.services.ai.recommendation_engine import RecommendationEngine
from backend_core.services.ai.ai_alert_engine import AIAlertEngine
from shared.config import get_settings
from shared.database.session import get_db
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/api/v1/ai", tags=["ai-business-logic"])


@router.get("/recommendations", summary="Get retail optimizations and layout suggestions")
def get_recommendations(
    store_id: Optional[str] = Query(default=None, description="Store external ID"),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """
    Returns AI-generated structured recommendations for marketing, layout,
    staffing, VIP engagement, and product placements.
    """
    sid = store_id or tenant.store_external_id
    engine = RecommendationEngine(db, tenant.brand_id)
    recs = engine.generate_recommendations(sid)
    
    return {
        "store_id": sid,
        "recommendations": recs
    }


@router.post("/alerts/evaluate", summary="Trigger manual evaluation of AI alert rules (diagnostic)")
def trigger_alert_evaluation(
    store_id: Optional[str] = Query(default=None),
    footfall: int = Query(default=20),
    transactions: int = Query(default=0),
    queue_count: int = Query(default=5),
    employee_name: str = Query(default="Rohan Kumar"),
    duration_minutes: float = Query(default=25.0),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("admin")),
):
    """
    Diagnostic endpoint to manually trigger and test AI alert evaluations:
    - Low conversion (combining footfall & transactions parameters)
    - Long queue (evaluating queue_count parameter)
    - Employee inactivity (evaluating employee_name & duration parameters)
    """
    sid = store_id or tenant.store_external_id
    engine = AIAlertEngine(db, get_settings(), tenant.brand_id)
    
    triggered = []
    
    # 1. Check conversion
    alert_conv = engine.check_low_conversion(sid, footfall, transactions)
    if alert_conv:
        triggered.append({"type": "low_conversion", "id": str(alert_conv.id)})
        
    # 2. Check queue
    alert_queue = engine.check_long_queue(sid, "Checkout counter 1", queue_count)
    if alert_queue:
        triggered.append({"type": "long_queue", "id": str(alert_queue.id)})
        
    # 3. Check employee inactivity
    alert_emp = engine.check_employee_inactivity(sid, employee_name, "Gold Section Display", duration_minutes)
    if alert_emp:
        triggered.append({"type": "employee_inactivity", "id": str(alert_emp.id)})
        
    return {
        "status": "success",
        "evaluated_store": sid,
        "alerts_triggered": triggered
    }
