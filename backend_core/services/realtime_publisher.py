"""
Realtime event publisher — Module 2 (Phase 4).

Publishes structured events to Redis channels consumed by SSE endpoints.
Works in both sync and async contexts; publishes fire-and-forget.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Channel naming conventions
# events:{brand_id}:{store_id}     — visitor/recognition events
# camera_health:{brand_id}         — camera online/offline events
# alerts:{store_id}                — alert notifications (used by existing ws/live)

EVENT_TYPES = frozenset(
    {
        "visitor_entered",
        "visitor_exited",
        "recognition_detected",
        "vip_detected",
        "camera_offline",
        "camera_online",
        "alert_generated",
    }
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_event(event_type: str, payload: dict[str, Any]) -> str:
    return json.dumps(
        {
            "type": event_type,
            "payload": payload,
            "ts": _utcnow_iso(),
        },
        default=str,
    )


# ---------------------------------------------------------------------------
# Sync publisher (used from sync FastAPI endpoint handlers / edge ingest)
# ---------------------------------------------------------------------------

class RealtimePublisher:
    """
    Sync wrapper around Redis PUBLISH.

    Gracefully no-ops when Redis is not configured.
    """

    def __init__(self, redis_url: Optional[str] = None) -> None:
        self._url = redis_url
        self._client: Any = None

    def _get_client(self):
        if self._client is None and self._url:
            try:
                import redis  # type: ignore

                self._client = redis.from_url(self._url, decode_responses=True)
            except Exception as exc:
                logger.warning("RealtimePublisher: Redis unavailable — %s", exc)
        return self._client

    def publish_event(
        self,
        brand_id: uuid.UUID,
        store_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        if event_type not in EVENT_TYPES:
            logger.debug("Unknown event type %s, skipping", event_type)
            return
        channel = f"events:{brand_id}:{store_id}"
        message = _build_event(event_type, payload)
        self._publish(channel, message)
        # Also fan out to alerts channel for dashboard WS compatibility
        if event_type == "alert_generated":
            self._publish(f"alerts:{store_id}", message)

    def publish_camera_health(
        self,
        brand_id: uuid.UUID,
        camera_id: str,
        status: str,  # "online" | "offline"
        store_id: Optional[str] = None,
    ) -> None:
        event_type = "camera_online" if status == "online" else "camera_offline"
        channel = f"camera_health:{brand_id}"
        message = _build_event(
            event_type,
            {"camera_id": camera_id, "store_id": store_id, "status": status},
        )
        self._publish(channel, message)

    def _publish(self, channel: str, message: str) -> None:
        client = self._get_client()
        if client:
            try:
                client.publish(channel, message)
            except Exception as exc:
                logger.debug("Redis PUBLISH failed: %s", exc)


# ---------------------------------------------------------------------------
# Async publisher (used by SSE tasks / background coroutines)
# ---------------------------------------------------------------------------

class AsyncRealtimePublisher:
    """Async version of RealtimePublisher using redis.asyncio."""

    def __init__(self, redis_url: Optional[str] = None) -> None:
        self._url = redis_url
        self._client: Any = None

    async def _get_client(self):
        if self._client is None and self._url:
            try:
                import redis.asyncio as aioredis  # type: ignore

                self._client = aioredis.from_url(self._url, decode_responses=True)
            except Exception as exc:
                logger.warning("AsyncRealtimePublisher: Redis unavailable — %s", exc)
        return self._client

    async def publish(self, channel: str, event_type: str, payload: dict[str, Any]) -> None:
        client = await self._get_client()
        if client:
            try:
                message = _build_event(event_type, payload)
                await client.publish(channel, message)
            except Exception as exc:
                logger.debug("Async Redis PUBLISH failed: %s", exc)

    async def ping(self) -> bool:
        client = await self._get_client()
        if client:
            try:
                return await client.ping()
            except Exception:
                return False
        return False


# ---------------------------------------------------------------------------
# Singleton accessor (lazy-initialised per process)
# ---------------------------------------------------------------------------

_publisher: Optional[RealtimePublisher] = None


def get_publisher(redis_url: Optional[str] = None) -> RealtimePublisher:
    global _publisher
    if _publisher is None:
        _publisher = RealtimePublisher(redis_url)
    return _publisher
