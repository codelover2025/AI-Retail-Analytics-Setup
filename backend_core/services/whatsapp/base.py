"""
WhatsApp provider abstract base class — Module 6 (Phase 4).

Provider abstraction allows swapping between Meta Cloud API,
Twilio, or other WABA providers without changing business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class WhatsAppProvider(ABC):
    """Abstract WhatsApp Business API provider."""

    @abstractmethod
    def send_text(self, *, to: str, message: str) -> dict[str, Any]:
        """Send a plain text message to a WhatsApp number."""
        ...

    @abstractmethod
    def send_template(
        self,
        *,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        """Send a pre-approved template message."""
        ...

    def send_daily_report(self, *, to: str, summary: dict[str, Any]) -> dict[str, Any]:
        """
        Send a formatted daily analytics report summary.
        Falls back to text if template not available.
        """
        lines = [
            "📊 *Daily Retail Analytics Report*",
            f"Total Visitors: {summary.get('total_visitors', 0)}",
            f"Repeat Visitors: {summary.get('repeat_visitors', 0)}",
            f"Avg Dwell: {summary.get('avg_dwell_seconds', 0):.0f}s",
            f"Staff Interactions: {summary.get('staff_interactions', 0)}",
        ]
        return self.send_text(to=to, message="\n".join(lines))

    def send_vip_alert(
        self, *, to: str, store_id: str, camera_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Send VIP arrival notification."""
        msg = f"👑 *VIP Arrival Alert*\nStore: {store_id}"
        if camera_id:
            msg += f"\nCamera: {camera_id}"
        return self.send_text(to=to, message=msg)

    def send_crowd_alert(
        self, *, to: str, store_id: str, count: int, threshold: int
    ) -> dict[str, Any]:
        """Send high crowd density alert."""
        msg = (
            f"🚨 *High Crowd Alert*\n"
            f"Store: {store_id}\n"
            f"Current: {count} visitors (Threshold: {threshold})"
        )
        return self.send_text(to=to, message=msg)


class StubWhatsAppProvider(WhatsAppProvider):
    """No-op provider — logs messages without sending (for dev/test)."""

    import logging
    _log = logging.getLogger("whatsapp.stub")

    def send_text(self, *, to: str, message: str) -> dict[str, Any]:
        self._log.info("[WhatsApp STUB] To: %s | %s", to, message[:80])
        return {"status": "stub", "to": to}

    def send_template(
        self,
        *,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        self._log.info("[WhatsApp STUB] Template '%s' → %s", template_name, to)
        return {"status": "stub", "to": to, "template": template_name}
