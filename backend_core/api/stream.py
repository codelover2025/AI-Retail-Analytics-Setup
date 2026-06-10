"""
SSE streaming endpoints — Module 2 (Phase 4).

Endpoints:
  GET /stream/live-visitors   — SSE; live visitor count (polls DB or Redis)
  GET /stream/events          — SSE; visitor/recognition/alert events
  GET /stream/camera-health   — SSE; camera online/offline events

All endpoints:
  - Send SSE `retry: 3000` for automatic client reconnect
  - Send heartbeat every 30s to keep connection alive
  - Fall back to polling when Redis is not configured
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.config import get_settings
from shared.database.models import LiveVisitor
from shared.database.session import get_db
from shared.tenant_context import TenantContext
from backend_core.auth.dependencies import get_tenant_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["realtime"])

HEARTBEAT_INTERVAL = 30  # seconds
POLL_INTERVAL = 5         # seconds (fallback polling)


def _sse_message(event: str, data: dict) -> str:
    payload = json.dumps(data, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


def _sse_heartbeat() -> str:
    return "event: heartbeat\ndata: {}\n\n"


def _sse_retry() -> str:
    return "retry: 3000\n\n"


# ---------------------------------------------------------------------------
# /stream/live-visitors
# ---------------------------------------------------------------------------

async def _live_visitors_generator(
    redis_url: Optional[str],
    brand_id,
    store_id: str,
    db: Session,
) -> AsyncGenerator[str, None]:
    yield _sse_retry()

    if redis_url:
        try:
            import redis.asyncio as aioredis  # type: ignore

            r = aioredis.from_url(redis_url, decode_responses=True)
            pubsub = r.pubsub()
            channel = f"events:{brand_id}:{store_id}"
            await pubsub.subscribe(channel)
            last_heartbeat = asyncio.get_event_loop().time()

            while True:
                now = asyncio.get_event_loop().time()
                if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                    yield _sse_heartbeat()
                    last_heartbeat = now

                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg.get("type") == "message":
                    try:
                        data = json.loads(msg["data"])
                        if data.get("type") in ("visitor_entered", "visitor_exited"):
                            yield _sse_message("live_update", data)
                    except json.JSONDecodeError:
                        pass
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.debug("SSE live-visitors Redis error: %s", exc)

    # Polling fallback
    last_count = -1
    while True:
        try:
            stmt = select(func.count(LiveVisitor.id)).where(
                LiveVisitor.brand_id == brand_id,
                LiveVisitor.store_id == store_id,
            )
            count = db.execute(stmt).scalar_one() or 0
            if count != last_count:
                yield _sse_message(
                    "live_visitors",
                    {"count": count, "store_id": store_id},
                )
                last_count = count
        except Exception as exc:
            logger.debug("SSE live-visitors poll error: %s", exc)

        await asyncio.sleep(POLL_INTERVAL)


@router.get("/live-visitors", summary="SSE: live visitor count stream")
async def live_visitors_stream(
    store_id: Optional[str] = Query(default=None),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """
    Server-Sent Events stream delivering live visitor counts.

    Clients should use `EventSource` or `fetch` with `stream: true`.
    Auto-reconnects via `retry: 3000` directive.
    """
    settings = get_settings()
    sid = store_id or tenant.store_external_id

    return StreamingResponse(
        _live_visitors_generator(settings.redis_url, tenant.brand_id, sid, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# /stream/events
# ---------------------------------------------------------------------------

async def _events_generator(
    redis_url: Optional[str],
    brand_id,
    store_id: str,
    event_filter: Optional[str],
) -> AsyncGenerator[str, None]:
    yield _sse_retry()
    allowed = set(event_filter.split(",")) if event_filter else None

    if redis_url:
        try:
            import redis.asyncio as aioredis  # type: ignore

            r = aioredis.from_url(redis_url, decode_responses=True)
            pubsub = r.pubsub()
            channel = f"events:{brand_id}:{store_id}"
            await pubsub.subscribe(channel)
            last_heartbeat = asyncio.get_event_loop().time()

            while True:
                now = asyncio.get_event_loop().time()
                if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                    yield _sse_heartbeat()
                    last_heartbeat = now

                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg.get("type") == "message":
                    try:
                        data = json.loads(msg["data"])
                        evt = data.get("type", "")
                        if allowed is None or evt in allowed:
                            yield _sse_message(evt, data)
                    except json.JSONDecodeError:
                        pass
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.debug("SSE events Redis error: %s", exc)

    # Heartbeat-only fallback
    while True:
        yield _sse_heartbeat()
        await asyncio.sleep(HEARTBEAT_INTERVAL)


@router.get("/events", summary="SSE: realtime event stream")
async def events_stream(
    store_id: Optional[str] = Query(default=None),
    event_types: Optional[str] = Query(
        default=None,
        description="Comma-separated event type filter: visitor_entered,visitor_exited,vip_detected,...",
    ),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """
    SSE stream for realtime retail events.

    Supported event types:
    - `visitor_entered` / `visitor_exited`
    - `recognition_detected` / `vip_detected`
    - `alert_generated`
    """
    settings = get_settings()
    sid = store_id or tenant.store_external_id

    return StreamingResponse(
        _events_generator(settings.redis_url, tenant.brand_id, sid, event_types),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# /stream/camera-health
# ---------------------------------------------------------------------------

async def _camera_health_generator(
    redis_url: Optional[str],
    brand_id,
) -> AsyncGenerator[str, None]:
    yield _sse_retry()

    if redis_url:
        try:
            import redis.asyncio as aioredis  # type: ignore

            r = aioredis.from_url(redis_url, decode_responses=True)
            pubsub = r.pubsub()
            channel = f"camera_health:{brand_id}"
            await pubsub.subscribe(channel)
            last_heartbeat = asyncio.get_event_loop().time()

            while True:
                now = asyncio.get_event_loop().time()
                if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                    yield _sse_heartbeat()
                    last_heartbeat = now

                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg.get("type") == "message":
                    try:
                        data = json.loads(msg["data"])
                        evt = data.get("type", "camera_health")
                        yield _sse_message(evt, data)
                    except json.JSONDecodeError:
                        pass
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.debug("SSE camera-health Redis error: %s", exc)

    while True:
        yield _sse_heartbeat()
        await asyncio.sleep(HEARTBEAT_INTERVAL)


@router.get("/camera-health", summary="SSE: camera online/offline events")
async def camera_health_stream(
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """
    SSE stream for camera connectivity events.

    Event types: `camera_online`, `camera_offline`.
    """
    settings = get_settings()

    return StreamingResponse(
        _camera_health_generator(settings.redis_url, tenant.brand_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
