import uuid

from sqlalchemy.orm import Session

from shared.config import Settings
from shared.database.tenant_repository import TenantRepository


def resolve_brand_id(db: Session, settings: Settings) -> uuid.UUID:
    if settings.brand_id:
        return uuid.UUID(settings.brand_id)
    brand = TenantRepository(db).get_brand_by_slug(settings.brand_slug)
    if brand is None:
        raise RuntimeError(
            f"Brand not found: {settings.brand_slug}. Run: python scripts/seed_phase1.py"
        )
    return brand.id
