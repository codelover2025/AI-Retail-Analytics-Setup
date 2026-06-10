"""
WhatsApp provider factory — Module 6 (Phase 4).

Returns the configured provider from settings.
Defaults to StubProvider when credentials are absent.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.config import Settings

from backend_core.services.whatsapp.base import StubWhatsAppProvider, WhatsAppProvider

logger = logging.getLogger(__name__)


def get_whatsapp_provider(settings: "Settings") -> WhatsAppProvider:
    """
    Factory function — returns the configured WhatsApp provider.

    Provider selection:
      WHATSAPP_PROVIDER=meta  → MetaWhatsAppProvider (requires credentials)
      WHATSAPP_PROVIDER=stub  → StubWhatsAppProvider (no-op, for testing)
      (default fallback)      → StubWhatsAppProvider

    If provider=meta but credentials are missing, falls back to stub
    with a warning rather than crashing.
    """
    provider = getattr(settings, "whatsapp_provider", "stub")

    if provider == "meta":
        phone_id = getattr(settings, "whatsapp_phone_number_id", None)
        token = getattr(settings, "whatsapp_access_token", None)

        if not phone_id or not token:
            logger.warning(
                "WhatsApp provider=meta but WHATSAPP_PHONE_NUMBER_ID or "
                "WHATSAPP_ACCESS_TOKEN not set — falling back to stub provider"
            )
            return StubWhatsAppProvider()

        from backend_core.services.whatsapp.meta_provider import MetaWhatsAppProvider
        return MetaWhatsAppProvider(
            phone_number_id=phone_id,
            access_token=token,
            api_version=getattr(settings, "whatsapp_api_version", "v19.0"),
        )

    return StubWhatsAppProvider()
