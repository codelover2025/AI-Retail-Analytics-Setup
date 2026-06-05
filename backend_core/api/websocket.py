import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from shared.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/live")
async def live_updates(websocket: WebSocket, store_id: Optional[str] = None):
    """
    Real-time alert stream via Redis pub/sub.
    Falls back to heartbeat polling when Redis is not configured.
    """
    await websocket.accept()
    settings = get_settings()
    target_store = store_id or settings.store_id

    if settings.redis_url:
        await _redis_listener(websocket, settings.redis_url, target_store)
    else:
        await _heartbeat_loop(websocket)


async def _redis_listener(websocket: WebSocket, redis_url: str, store_id: str) -> None:
    import redis.asyncio as aioredis

    client = aioredis.from_url(redis_url, decode_responses=True)
    pubsub = client.pubsub()
    channel = f"alerts:{store_id}"
    await pubsub.subscribe(channel)

    async def receive_loop():
        try:
            while True:
                await websocket.receive()
        except Exception:
            pass

    receive_task = asyncio.create_task(receive_loop())
    try:
        while not receive_task.done():
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    finally:
        receive_task.cancel()
        await pubsub.unsubscribe(channel)
        await client.close()


async def _heartbeat_loop(websocket: WebSocket) -> None:
    try:
        while True:
            await websocket.send_json({"type": "heartbeat"})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
