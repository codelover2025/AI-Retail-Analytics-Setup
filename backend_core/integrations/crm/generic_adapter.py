"""Generic REST CRM adapter — Module 9 (Phase 4)."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from backend_core.integrations.crm.base import CRMAdapter, CRMCustomerProfile

logger = logging.getLogger(__name__)


class GenericCRMAdapter(CRMAdapter):
    """REST-based generic CRM adapter."""

    def __init__(self, api_url: str, api_key: Optional[str] = None, timeout: float = 10.0) -> None:
        self._url = api_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._timeout = timeout

    def lookup_customer(self, visitor_id: str) -> Optional[CRMCustomerProfile]:
        try:
            resp = httpx.get(
                f"{self._url}/customers/lookup",
                headers=self._headers,
                params={"visitor_id": visitor_id},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            c = resp.json()
            return CRMCustomerProfile(
                external_id=str(c.get("id", visitor_id)),
                name=c.get("name"),
                email=c.get("email"),
                phone=c.get("phone"),
                loyalty_points=int(c.get("loyalty_points", 0)),
                loyalty_tier=c.get("loyalty_tier"),
                is_vip=bool(c.get("is_vip", False)),
                extra=c,
            )
        except Exception as exc:
            logger.debug("CRM lookup_customer failed: %s", exc)
            return None

    def get_loyalty(self, customer_external_id: str) -> dict[str, Any]:
        try:
            resp = httpx.get(
                f"{self._url}/customers/{customer_external_id}/loyalty",
                headers=self._headers,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("CRM get_loyalty failed: %s", exc)
            return {"error": str(exc)}

    def update_points(self, customer_external_id: str, delta: int) -> dict[str, Any]:
        try:
            resp = httpx.post(
                f"{self._url}/customers/{customer_external_id}/points",
                headers=self._headers,
                json={"delta": delta},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("CRM update_points failed: %s", exc)
            return {"error": str(exc)}


class StubCRMAdapter(CRMAdapter):
    def lookup_customer(self, visitor_id: str) -> Optional[CRMCustomerProfile]:
        logger.info("[CRM STUB] lookup_customer: %s", visitor_id)
        return None

    def get_loyalty(self, customer_external_id: str) -> dict[str, Any]:
        return {"status": "stub", "loyalty_points": 0}

    def update_points(self, customer_external_id: str, delta: int) -> dict[str, Any]:
        return {"status": "stub", "delta": delta}
