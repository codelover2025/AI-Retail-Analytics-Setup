from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import verify_dashboard_api_key
from backend_core.auth.jwt_tokens import create_access_token
from shared.config import Settings, get_settings
from shared.database.session import get_db
from shared.database.tenant_repository import TenantRepository

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    brand_slug: str
    store_id: str
    subject: str = "dashboard"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    brand_slug: str
    store_id: str


@router.post("/token", response_model=TokenResponse, dependencies=[Depends(verify_dashboard_api_key)])
def issue_token(
    body: TokenRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Issue JWT for dashboard (protect with API_KEY in production)."""
    tenants = TenantRepository(db)
    brand = tenants.get_brand_by_slug(body.brand_slug)
    if brand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Brand not found")
    store = tenants.get_store(brand.id, body.store_id)
    if store is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Store not found")

    token = create_access_token(
        settings,
        subject=body.subject,
        brand_id=str(brand.id),
        brand_slug=brand.slug,
        extra={"store_id": store.external_id},
    )
    return TokenResponse(
        access_token=token,
        brand_slug=brand.slug,
        store_id=store.external_id,
    )
