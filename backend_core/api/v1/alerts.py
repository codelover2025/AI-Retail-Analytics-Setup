"""
Alerts API — Module 5 (Phase 4).

Endpoints:
  GET    /api/alerts              — list alerts (filterable, paginated)
  POST   /api/alerts/{id}/acknowledge
  GET    /api/alerts/rules        — list alert rules
  POST   /api/alerts/rules        — create alert rule
  PATCH  /api/alerts/rules/{id}   — update alert rule
  DELETE /api/alerts/rules/{id}   — delete alert rule
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.auth.rbac import UserContext, require_role
from shared.database.alert_rule_models import AlertRule
from shared.database.models import Alert
from shared.database.session import get_db
from shared.schemas.pagination import paginate
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AlertRuleCreate(BaseModel):
    alert_type: str = Field(..., description="vip_detected|watchlist_detected|camera_offline|low_traffic|high_crowd")
    store_id: Optional[str] = None
    threshold: Optional[float] = None
    channels: list[str] = Field(default_factory=lambda: ["dashboard"])
    recipients: list[str] = Field(default_factory=list)
    config: dict = Field(default_factory=dict)


class AlertRuleUpdate(BaseModel):
    threshold: Optional[float] = None
    channels: Optional[list[str]] = None
    recipients: Optional[list[str]] = None
    enabled: Optional[bool] = None
    config: Optional[dict] = None


# ---------------------------------------------------------------------------
# Alert list
# ---------------------------------------------------------------------------

@router.get("", summary="List alerts (filterable, paginated)")
def list_alerts(
    store_id: Optional[str] = Query(default=None),
    alert_type: Optional[str] = Query(default=None),
    acknowledged: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    stmt = select(Alert).where(Alert.brand_id == tenant.brand_id)
    if store_id:
        stmt = stmt.where(Alert.store_id == store_id)
    if alert_type:
        stmt = stmt.where(Alert.alert_type == alert_type)
    if acknowledged is not None:
        stmt = stmt.where(Alert.acknowledged == acknowledged)

    total = db.scalar(stmt.with_only_columns(Alert.id).order_by(None).limit(None))  # type: ignore
    total = db.scalar(select(Alert.id).where(Alert.brand_id == tenant.brand_id)) and \
            db.execute(stmt.with_only_columns(Alert.id)).rowcount

    # Use count subquery
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = db.scalar(count_stmt) or 0

    data_stmt = (
        stmt.order_by(Alert.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list(db.scalars(data_stmt).all())

    items = [
        {
            "id": str(r.id),
            "alert_type": r.alert_type,
            "store_id": r.store_id,
            "message": r.message,
            "acknowledged": r.acknowledged,
            "created_at": r.created_at.isoformat(),
            "payload": r.payload,
        }
        for r in rows
    ]
    return paginate(items, total=total_count, page=page, page_size=page_size)


@router.post("/{alert_id}/acknowledge", summary="Acknowledge an alert")
def acknowledge_alert(
    alert_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("store_manager")),
):
    alert = db.get(Alert, alert_id)
    if alert is None or alert.brand_id != tenant.brand_id:
        raise HTTPException(404, "Alert not found")
    alert.acknowledged = True
    db.commit()
    return {"id": str(alert.id), "acknowledged": True}
def invalidate_rules_cache(brand_id: uuid.UUID) -> None:
    try:
        from shared.config import get_settings
        settings = get_settings()
        if settings.redis_url:
            import redis
            r = redis.from_url(settings.redis_url)
            pattern = f"alert_rules:{brand_id}:*"
            keys_to_delete = r.keys(pattern)
            if keys_to_delete:
                r.delete(*keys_to_delete)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Alert Rules
# ---------------------------------------------------------------------------

@router.get("/rules", summary="List alert rules")
def list_rules(
    store_id: Optional[str] = Query(default=None),
    alert_type: Optional[str] = Query(default=None),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("store_manager")),
):
    stmt = select(AlertRule).where(AlertRule.brand_id == tenant.brand_id)
    if store_id:
        stmt = stmt.where(AlertRule.store_id == store_id)
    if alert_type:
        stmt = stmt.where(AlertRule.alert_type == alert_type)
    stmt = stmt.order_by(AlertRule.created_at.desc())

    rules = list(db.scalars(stmt).all())
    return [
        {
            "id": str(r.id),
            "alert_type": r.alert_type,
            "store_id": r.store_id,
            "threshold": r.threshold,
            "channels": r.channels,
            "recipients": r.recipients,
            "enabled": r.enabled,
            "config": r.config,
        }
        for r in rules
    ]


@router.post("/rules", status_code=201, summary="Create alert rule")
def create_rule(
    body: AlertRuleCreate,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("brand_admin")),
):
    valid_types = {
        "vip_detected", "watchlist_detected", "camera_offline", "low_traffic", "high_crowd"
    }
    if body.alert_type not in valid_types:
        raise HTTPException(400, f"alert_type must be one of {valid_types}")

    rule = AlertRule(
        brand_id=tenant.brand_id,
        store_id=body.store_id,
        alert_type=body.alert_type,
        threshold=body.threshold,
        channels=body.channels,
        recipients=body.recipients,
        config=body.config,
        enabled=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    invalidate_rules_cache(tenant.brand_id)
    return {"id": str(rule.id), "alert_type": rule.alert_type, "enabled": rule.enabled}


@router.patch("/rules/{rule_id}", summary="Update alert rule")
def update_rule(
    rule_id: uuid.UUID,
    body: AlertRuleUpdate,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("brand_admin")),
):
    rule = db.get(AlertRule, rule_id)
    if rule is None or rule.brand_id != tenant.brand_id:
        raise HTTPException(404, "Alert rule not found")
    if body.threshold is not None:
        rule.threshold = body.threshold
    if body.channels is not None:
        rule.channels = body.channels
    if body.recipients is not None:
        rule.recipients = body.recipients
    if body.enabled is not None:
        rule.enabled = body.enabled
    if body.config is not None:
        rule.config = body.config
    db.commit()
    invalidate_rules_cache(tenant.brand_id)
    return {"id": str(rule.id), "updated": True}


@router.delete("/rules/{rule_id}", status_code=204, summary="Delete alert rule")
def delete_rule(
    rule_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("brand_admin")),
):
    rule = db.get(AlertRule, rule_id)
    if rule is None or rule.brand_id != tenant.brand_id:
        raise HTTPException(404, "Alert rule not found")
    db.delete(rule)
    db.commit()
    invalidate_rules_cache(tenant.brand_id)
    return Response(status_code=204)
