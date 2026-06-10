"""POS adapter factory."""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from shared.config import Settings
from backend_core.integrations.pos.base import POSAdapter

def get_pos_adapter(settings: "Settings") -> POSAdapter:
    provider = getattr(settings, "pos_provider", None)
    if provider == "generic":
        from backend_core.integrations.pos.generic_adapter import GenericPOSAdapter
        return GenericPOSAdapter(
            api_url=settings.pos_api_url or "",
            api_key=getattr(settings, "pos_api_key", None),
        )
    from backend_core.integrations.pos.generic_adapter import StubPOSAdapter
    return StubPOSAdapter()
