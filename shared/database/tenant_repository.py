import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from shared.database.tenant_models import Brand, Camera, EdgeDevice, Store
from shared.security import verify_secret


class TenantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_brand_by_slug(self, slug: str) -> Optional[Brand]:
        return self.db.scalar(
            select(Brand).where(Brand.slug == slug, Brand.is_active.is_(True))
        )

    def get_store(self, brand_id: uuid.UUID, external_id: str) -> Optional[Store]:
        return self.db.scalar(
            select(Store).where(
                Store.brand_id == brand_id,
                Store.external_id == external_id,
                Store.is_active.is_(True),
            )
        )

    def get_store_with_cameras(self, brand_id: uuid.UUID, external_id: str) -> Optional[Store]:
        return self.db.scalar(
            select(Store)
            .options(joinedload(Store.cameras))
            .where(
                Store.brand_id == brand_id,
                Store.external_id == external_id,
                Store.is_active.is_(True),
            )
        )

    def list_enabled_cameras(self, store_id: uuid.UUID) -> list[Camera]:
        return list(
            self.db.scalars(
                select(Camera).where(
                    Camera.store_id == store_id,
                    Camera.enabled.is_(True),
                )
            ).all()
        )

    def authenticate_edge_device(self, api_key: str) -> Optional[EdgeDevice]:
        from shared.security import hash_secret
        hashed_key = hash_secret(api_key)
        return self.db.scalar(
            select(EdgeDevice).where(EdgeDevice.api_key_hash == hashed_key)
        )

    def get_edge_device_with_store(self, device_id: uuid.UUID) -> Optional[EdgeDevice]:
        return self.db.scalar(
            select(EdgeDevice)
            .options(joinedload(EdgeDevice.store).joinedload(Store.brand))
            .where(EdgeDevice.id == device_id)
        )
