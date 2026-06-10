"""HRMS adapter factory."""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from shared.config import Settings
from backend_core.integrations.hrms.base import HRMSAdapter

def get_hrms_adapter(settings: "Settings") -> HRMSAdapter:
    provider = getattr(settings, "hrms_provider", None)
    if provider == "generic":
        from backend_core.integrations.hrms.generic_adapter import GenericHRMSAdapter
        return GenericHRMSAdapter(
            api_url=settings.hrms_api_url or "",
            api_key=getattr(settings, "hrms_api_key", None),
        )
    from backend_core.integrations.hrms.generic_adapter import StubHRMSAdapter
    return StubHRMSAdapter()
