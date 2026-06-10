"""POS integration adapter base — Module 8 (Phase 4)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class POSTransaction:
    """Normalized POS transaction from any provider."""
    def __init__(
        self,
        external_id: str,
        store_id: str,
        amount: float,
        items_count: int = 1,
        timestamp: Optional[str] = None,
        visitor_id: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> None:
        self.external_id = external_id
        self.store_id = store_id
        self.amount = amount
        self.items_count = items_count
        self.timestamp = timestamp
        self.visitor_id = visitor_id
        self.extra = extra or {}


class POSAdapter(ABC):
    """Abstract POS integration adapter."""

    @abstractmethod
    def ingest_transaction(self, transaction: POSTransaction) -> dict[str, Any]:
        """Persist a single POS transaction."""
        ...

    @abstractmethod
    def sync_transactions(
        self,
        store_id: str,
        from_date: str,
        to_date: str,
    ) -> list[POSTransaction]:
        """Pull transactions from POS system for a date range."""
        ...
