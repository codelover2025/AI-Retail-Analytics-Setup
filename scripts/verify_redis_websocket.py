"""Test Redis pub/sub → WebSocket /ws/live (requires API + Redis)."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import get_settings


async def main() -> int:
    settings = get_settings()
    if not settings.redis_url:
        print("SKIP: REDIS_URL not set in .env")
        return 0

    try:
        import redis.asyncio as aioredis
        import websockets
    except ImportError as exc:
        print(f"SKIP: pip install redis websockets — {exc}")
        return 0

    store_id = settings.store_id
    channel = f"alerts:{store_id}"
    payload = json.dumps({"type": "test_alert", "message": "redis websocket handoff test"})

    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    await client.publish(channel, payload)
    await client.close()
    print(f"Published to Redis channel: {channel}")

    ws_url = f"ws://localhost:8000/ws/live?store_id={store_id}"
    try:
        async with websockets.connect(ws_url, open_timeout=5) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=8)
            if "test_alert" in msg or "handoff" in msg:
                print(f"PASS: WebSocket received: {msg[:120]}")
                return 0
            if "heartbeat" in msg:
                print("WARN: got heartbeat fallback — is API using REDIS_URL? Restart uvicorn after setting REDIS_URL")
                return 1
            print(f"FAIL: unexpected message: {msg}")
            return 1
    except Exception as exc:
        print(f"FAIL: WebSocket test: {exc}")
        print("Ensure: docker compose up -d redis AND uvicorn restarted with REDIS_URL in .env")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
