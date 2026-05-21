import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    brand_id: uuid.UUID
    brand_slug: str
    store_external_id: str
    store_id: uuid.UUID
