import uuid
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from backend_core.auth.jwt_tokens import decode_access_token
from shared.config import Settings, get_settings
from shared.database.session import get_db
from shared.database.tenant_models import EdgeDevice
from shared.database.tenant_repository import TenantRepository
from shared.tenant_context import TenantContext

bearer_scheme = HTTPBearer(auto_error=False)


def _resolve_dashboard_api_key(
    x_api_key: Optional[str],
    api_key_query: Optional[str],
) -> Optional[str]:
    """Header X-API-Key preferred; ?api_key= for browser/Swagger quick tests."""
    return x_api_key or api_key_query


def verify_dashboard_api_key(
    x_api_key: Optional[str] = Header(default=None),
    api_key: Optional[str] = Query(default=None, description="Same as X-API-Key (browser dev)"),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security misconfiguration: Server API key is not set",
        )
    provided = _resolve_dashboard_api_key(x_api_key, api_key)
    if provided != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


def get_tenant_from_jwt(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TenantContext:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bearer token required")
    try:
        payload = decode_access_token(settings, credentials.credentials)
        brand_id_str = payload.get("brand_id")
        brand_slug = payload.get("brand_slug")
        
        # If super_admin and brand_id is empty, resolve to default brand from settings
        if not brand_id_str and payload.get("role") == "super_admin":
            from sqlalchemy import select
            from shared.database.tenant_models import Brand
            brand = db.scalar(select(Brand).where(Brand.slug == settings.brand_slug))
            if brand:
                brand_id_str = str(brand.id)
                brand_slug = brand.slug
                
        if not brand_id_str:
            raise ValueError("Token missing brand_id")
            
        brand_id = uuid.UUID(brand_id_str)
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc

    store_external = payload.get("store_id")
    # If store_id is empty, resolve it for brand_admin or super_admin roles
    if not store_external and payload.get("role") in ("brand_admin", "super_admin"):
        from sqlalchemy import select
        from shared.database.tenant_models import Store
        store = db.scalar(select(Store).where(Store.brand_id == brand_id).limit(1))
        if store:
            store_external = store.external_id
        else:
            store_external = settings.store_id
        
    if not store_external:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token missing store_id")

    store = None
    try:
        store_uuid = uuid.UUID(store_external)
        from shared.database.tenant_models import Store
        store = db.get(Store, store_uuid)
    except (ValueError, TypeError):
        store = TenantRepository(db).get_store(brand_id, store_external)

    if store is None or store.brand_id != brand_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Store not found for token")

    return TenantContext(
        brand_id=brand_id,
        brand_slug=brand_slug,
        store_external_id=store.external_id,
        store_id=store.id,
    )


def get_tenant_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    x_api_key: Optional[str] = Header(default=None),
    api_key: Optional[str] = Query(default=None),
    brand_slug_header: Optional[str] = Header(default=None, alias="X-Brand-Slug"),
    store_id_header: Optional[str] = Header(default=None, alias="X-Store-Id"),
    brand_slug: Optional[str] = Query(default=None),
    store_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TenantContext:
    """JWT preferred; fallback to API key + brand/store headers (dev / server-to-server)."""
    if credentials:
        return get_tenant_from_jwt(credentials, db, settings)

    verify_dashboard_api_key(x_api_key, api_key, settings)
    slug = brand_slug_header or brand_slug or settings.brand_slug
    ext_store = store_id_header or store_id or settings.store_id
    brand = TenantRepository(db).get_brand_by_slug(slug)
    if brand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Brand not found: {slug}")
    store = TenantRepository(db).get_store(brand.id, ext_store)
    if store is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Store not found: {ext_store}")
    return TenantContext(
        brand_id=brand.id,
        brand_slug=brand.slug,
        store_external_id=store.external_id,
        store_id=store.id,
    )


def get_edge_device(
    x_edge_key: str = Header(..., alias="X-Edge-Key"),
    db: Session = Depends(get_db),
) -> EdgeDevice:
    device = TenantRepository(db).authenticate_edge_device(x_edge_key)
    if device is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid edge API key")
    return device
