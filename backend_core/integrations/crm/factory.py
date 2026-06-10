"""CRM adapter factory."""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from shared.config import Settings
from backend_core.integrations.crm.base import CRMAdapter

def get_crm_adapter(settings: "Settings") -> CRMAdapter:
    provider = getattr(settings, "crm_provider", None)
    if provider == "generic":
        from backend_core.integrations.crm.generic_adapter import GenericCRMAdapter
        return GenericCRMAdapter(
            api_url=settings.crm_api_url or "",
            api_key=getattr(settings, "crm_api_key", None),
        )
    from backend_core.integrations.crm.generic_adapter import StubCRMAdapter
    return StubCRMAdapter()
