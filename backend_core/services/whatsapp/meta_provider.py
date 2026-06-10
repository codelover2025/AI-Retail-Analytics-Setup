"""
Meta Cloud API (WABA) WhatsApp provider — Module 6 (Phase 4).

Implements WhatsApp Business Cloud API v19.0+.
Reference: https://developers.facebook.com/docs/whatsapp/cloud-api/

Required settings:
  WHATSAPP_PHONE_NUMBER_ID — from Meta Business Manager
  WHATSAPP_ACCESS_TOKEN    — permanent or system user token
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from backend_core.services.whatsapp.base import WhatsAppProvider

logger = logging.getLogger(__name__)

META_API_BASE = "https://graph.facebook.com"


class MetaWhatsAppProvider(WhatsAppProvider):
    """Meta Cloud API provider for WhatsApp Business."""

    def __init__(
        self,
        phone_number_id: str,
        access_token: str,
        api_version: str = "v19.0",
        timeout: float = 10.0,
    ) -> None:
        self._phone_number_id = phone_number_id
        self._access_token = access_token
        self._api_version = api_version
        self._timeout = timeout
        self._url = f"{META_API_BASE}/{api_version}/{phone_number_id}/messages"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = httpx.post(
                self._url,
                json=payload,
                headers=self._headers(),
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Meta WhatsApp API error %s: %s",
                exc.response.status_code,
                exc.response.text[:200],
            )
            raise
        except Exception as exc:
            logger.error("Meta WhatsApp request failed: %s", exc)
            raise

    def send_text(self, *, to: str, message: str) -> dict[str, Any]:
        """Send a free-form text message (within 24h window)."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to.lstrip("+"),
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message,
            },
        }
        result = self._post(payload)
        logger.info("WhatsApp text sent to %s: message_id=%s", to, result.get("messages", [{}])[0].get("id"))
        return result

    def send_template(
        self,
        *,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        """Send a pre-approved template message."""
        template_payload: dict[str, Any] = {
            "name": template_name,
            "language": {"code": language_code},
        }
        if components:
            template_payload["components"] = components

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to.lstrip("+"),
            "type": "template",
            "template": template_payload,
        }
        result = self._post(payload)
        logger.info("WhatsApp template '%s' sent to %s", template_name, to)
        return result
