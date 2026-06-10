"""CRM integration adapter base — Module 9 (Phase 4)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class CRMCustomerProfile:
    """Normalized CRM customer profile from any provider."""
    def __init__(
        self,
        external_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        loyalty_points: int = 0,
        loyalty_tier: Optional[str] = None,
        is_vip: bool = False,
        extra: Optional[dict] = None,
    ) -> None:
        self.external_id = external_id
        self.name = name
        self.email = email
        self.phone = phone
        self.loyalty_points = loyalty_points
        self.loyalty_tier = loyalty_tier
        self.is_vip = is_vip
        self.extra = extra or {}


class CRMAdapter(ABC):
    """Abstract CRM integration adapter."""

    @abstractmethod
    def lookup_customer(self, visitor_id: str) -> Optional[CRMCustomerProfile]:
        """Lookup CRM profile by visitor/person ID."""
        ...

    @abstractmethod
    def get_loyalty(self, customer_external_id: str) -> dict[str, Any]:
        """Get loyalty status and points for a customer."""
        ...

    @abstractmethod
    def update_points(self, customer_external_id: str, delta: int) -> dict[str, Any]:
        """Add or subtract loyalty points."""
        ...
