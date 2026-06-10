"""
POS API — Module 8 (Phase 4).

Endpoints:
  POST /api/pos/transactions          — ingest sale transaction
  GET  /api/pos/transactions          — list transactions (paginated)
  GET  /api/pos/analytics             — conversion metrics
  POST /api/pos/sync                  — pull-sync from POS system
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.integrations.pos.base import POSTransaction
from backend_core.integrations.pos.factory import get_pos_adapter
from backend_core.services.conversion_service import ConversionService
from shared.config import get_settings
from shared.database.models import Visitor
from shared.database.pos_models import POSPurchase
from shared.database.session import get_db
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/api/pos", tags=["pos"])


class IngestTransactionRequest(BaseModel):
    transaction_external_id: str
    store_id: str
    amount: float = Field(gt=0)
    items_count: int = Field(default=1, ge=1)
    timestamp: Optional[datetime] = None
    visitor_id: Optional[str] = Field(default=None, description="UUID of matched visitor")


@router.post("/transactions", status_code=201, summary="Ingest POS transaction")
def ingest_transaction(
    body: IngestTransactionRequest,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """
    Persist a POS sale transaction linked to a visitor.

    If `visitor_id` is provided, the purchase is linked to that visitor
    for conversion analytics.  Deduplication by `transaction_external_id`.
    """
    # Dedup check
    existing = db.query(POSPurchase).filter(
        POSPurchase.transaction_external_id == body.transaction_external_id
    ).first()
    if existing:
        return {"id": str(existing.id), "status": "already_exists"}

    # Resolve visitor
    visitor_id = None
    if body.visitor_id:
        try:
            visitor_id = uuid.UUID(body.visitor_id)
            visitor = db.get(Visitor, visitor_id)
            if visitor is None or visitor.brand_id != tenant.brand_id:
                visitor_id = None
        except ValueError:
            visitor_id = None

    if visitor_id is None:
        # Create anonymous visitor for POS linkage
        visitor = Visitor(
            brand_id=tenant.brand_id,
            embedding=[],
            visit_count=0,
        )
        db.add(visitor)
        db.flush()
        visitor_id = visitor.id

    purchase = POSPurchase(
        brand_id=tenant.brand_id,
        store_id=body.store_id,
        visitor_id=visitor_id,
        transaction_external_id=body.transaction_external_id,
        amount=body.amount,
        items_count=body.items_count,
        timestamp=body.timestamp or datetime.now(timezone.utc),
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return {"id": str(purchase.id), "status": "created"}


@router.get("/transactions", summary="List POS transactions (paginated)")
def list_transactions(
    store_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    svc = ConversionService(db, get_settings(), tenant.brand_id)
    return svc.transaction_list(store_id=store_id, page=page, page_size=page_size)


@router.get("/analytics", summary="Conversion analytics: visitor → purchase")
def conversion_analytics(
    store_id: Optional[str] = Query(default=None),
    from_day: Optional[date] = Query(default=None),
    to_day: Optional[date] = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """
    Returns conversion metrics:
    - Visitor → Purchase conversion rate
    - Revenue per visitor
    - Store conversion % breakdown
    """
    svc = ConversionService(db, get_settings(), tenant.brand_id)
    return svc.conversion_analytics(
        store_id=store_id, from_day=from_day, to_day=to_day, days=days
    )


@router.post("/sync", summary="Pull-sync transactions from POS system")
def sync_from_pos(
    store_id: str = Query(...),
    from_date: date = Query(...),
    to_date: Optional[date] = Query(default=None),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """Trigger a pull-sync of transactions from the configured POS provider."""
    settings = get_settings()
    adapter = get_pos_adapter(settings)
    to_date = to_date or date.today()
    transactions = adapter.sync_transactions(
        store_id, str(from_date), str(to_date)
    )

    imported = 0
    for tx in transactions:
        existing = db.query(POSPurchase).filter(
            POSPurchase.transaction_external_id == tx.external_id
        ).first()
        if existing:
            continue
        # Anonymous visitor for synced txns without visitor linkage
        visitor = Visitor(brand_id=tenant.brand_id, embedding=[], visit_count=0)
        db.add(visitor)
        db.flush()
        purchase = POSPurchase(
            brand_id=tenant.brand_id,
            store_id=tx.store_id,
            visitor_id=visitor.id,
            transaction_external_id=tx.external_id,
            amount=tx.amount,
            items_count=tx.items_count,
        )
        db.add(purchase)
        imported += 1

    db.commit()
    return {"from_date": str(from_date), "to_date": str(to_date), "imported": imported}
