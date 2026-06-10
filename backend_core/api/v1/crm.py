"""
CRM API — Module 9 (Phase 4).

Endpoints:
  GET  /api/crm/customers/{visitor_id}          — CRM profile lookup
  GET  /api/crm/customers/{visitor_id}/loyalty  — loyalty + VIP status
  POST /api/crm/customers/{visitor_id}/points   — update loyalty points
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.integrations.crm.factory import get_crm_adapter
from shared.config import get_settings
from shared.database.session import get_db
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/api/crm", tags=["crm"])


class UpdatePointsRequest(BaseModel):
    delta: int = Field(..., description="Points to add (positive) or deduct (negative)")


@router.get("/customers/{visitor_id}", summary="CRM customer profile lookup")
def get_customer_profile(
    visitor_id: str,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """Look up a customer's CRM profile by their platform visitor ID."""
    settings = get_settings()
    adapter = get_crm_adapter(settings)
    profile = adapter.lookup_customer(visitor_id)
    if profile is None:
        raise HTTPException(404, "CRM profile not found for this visitor")
    return {
        "visitor_id": visitor_id,
        "crm_external_id": profile.external_id,
        "name": profile.name,
        "email": profile.email,
        "phone": profile.phone,
        "is_vip": profile.is_vip,
        "loyalty_tier": profile.loyalty_tier,
        "loyalty_points": profile.loyalty_points,
    }


@router.get("/customers/{visitor_id}/loyalty", summary="Loyalty status and points")
def get_loyalty(
    visitor_id: str,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """Return loyalty status, tier, and point balance."""
    settings = get_settings()
    adapter = get_crm_adapter(settings)
    profile = adapter.lookup_customer(visitor_id)
    if profile is None:
        raise HTTPException(404, "CRM profile not found")
    loyalty = adapter.get_loyalty(profile.external_id)
    return {
        "visitor_id": visitor_id,
        "crm_external_id": profile.external_id,
        "is_vip": profile.is_vip,
        **loyalty,
    }


@router.post("/customers/{visitor_id}/points", summary="Update loyalty points")
def update_points(
    visitor_id: str,
    body: UpdatePointsRequest,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """Add or deduct loyalty points for a customer."""
    settings = get_settings()
    adapter = get_crm_adapter(settings)
    profile = adapter.lookup_customer(visitor_id)
    if profile is None:
        raise HTTPException(404, "CRM profile not found")
    result = adapter.update_points(profile.external_id, body.delta)
    return {"visitor_id": visitor_id, "delta": body.delta, **result}
