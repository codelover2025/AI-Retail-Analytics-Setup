"""Generic REST POS adapter — Module 8 (Phase 4)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from backend_core.integrations.pos.base import POSAdapter, POSTransaction

logger = logging.getLogger(__name__)


class GenericPOSAdapter(POSAdapter):
    """
    REST-based generic POS adapter.

    Expects POS to expose:
      GET {base_url}/transactions?store_id=X&from_date=X&to_date=X
      POST {base_url}/transactions (optional — for webhook-based ingestion)
    """

    def __init__(self, api_url: str, api_key: Optional[str] = None, timeout: float = 15.0) -> None:
        self._url = api_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._timeout = timeout

    def ingest_transaction(self, transaction: POSTransaction) -> dict[str, Any]:
        return {
            "external_id": transaction.external_id,
            "store_id": transaction.store_id,
            "amount": transaction.amount,
            "items_count": transaction.items_count,
            "status": "accepted",
        }

    def sync_transactions(self, store_id: str, from_date: str, to_date: str) -> list[POSTransaction]:
        try:
            resp = httpx.get(
                f"{self._url}/transactions",
                headers=self._headers,
                params={"store_id": store_id, "from_date": from_date, "to_date": to_date},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            return [
                POSTransaction(
                    external_id=str(t.get("id", "")),
                    store_id=store_id,
                    amount=float(t.get("amount", 0)),
                    items_count=int(t.get("items_count", 1)),
                    timestamp=t.get("timestamp"),
                    visitor_id=t.get("visitor_id"),
                    extra=t,
                )
                for t in resp.json()
            ]
        except Exception as exc:
            logger.error("POS sync_transactions failed: %s", exc)
            return []


class StubPOSAdapter(POSAdapter):
    def ingest_transaction(self, transaction: POSTransaction) -> dict[str, Any]:
        logger.info("[POS STUB] ingest_transaction: %s", transaction.external_id)
        return {"status": "stub", "external_id": transaction.external_id}

    def sync_transactions(self, store_id: str, from_date: str, to_date: str) -> list[POSTransaction]:
        logger.info("[POS STUB] sync_transactions for %s", store_id)
        return []
