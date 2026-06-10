"""
Redis-backed async cache with transparent in-process fallback.

Usage:
    cache = RedisCache(redis_url=settings.redis_url, default_ttl=300)
    value = await cache.get_or_set("key", lambda: expensive_query(), ttl=60)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Awaitable, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# In-process fallback (same as Phase 1-3 _TTLCache, lifted to shared layer)
# ---------------------------------------------------------------------------

class _InProcessCache:
    def __init__(self, ttl_seconds: int = 60) -> None:
        self.ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if not entry:
            return None
        ts, value = entry
        if time.monotonic() - ts > self.ttl:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._store[key] = (time.monotonic(), value)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear_prefix(self, prefix: str) -> None:
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]


# ---------------------------------------------------------------------------
# Redis-backed async cache
# ---------------------------------------------------------------------------

class RedisCache:
    """
    Async cache backed by Redis when available, in-process dict otherwise.

    Serialises values as JSON.  Not suitable for raw binary blobs.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 300,
    ) -> None:
        self._redis_url = redis_url
        self._default_ttl = default_ttl
        self._local = _InProcessCache(ttl_seconds=default_ttl)
        self._redis: Any = None  # lazy-initialised

    async def _get_redis(self):
        if self._redis is None and self._redis_url:
            try:
                import redis.asyncio as aioredis  # type: ignore
                self._redis = aioredis.from_url(
                    self._redis_url, decode_responses=True
                )
            except Exception as exc:
                logger.warning("Redis unavailable, falling back to in-process cache: %s", exc)
        return self._redis

    async def get(self, key: str) -> Any | None:
        r = await self._get_redis()
        if r:
            try:
                raw = await r.get(key)
                if raw is not None:
                    return json.loads(raw)
            except Exception as exc:
                logger.debug("Redis GET error: %s", exc)
        return self._local.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        effective_ttl = ttl or self._default_ttl
        r = await self._get_redis()
        if r:
            try:
                await r.setex(key, effective_ttl, json.dumps(value, default=str))
            except Exception as exc:
                logger.debug("Redis SET error: %s", exc)
        self._local.set(key, value)

    async def delete(self, key: str) -> None:
        r = await self._get_redis()
        if r:
            try:
                await r.delete(key)
            except Exception:
                pass
        self._local.delete(key)

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[T] | T],
        ttl: int | None = None,
    ) -> T:
        cached = await self.get(key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        import asyncio
        result = factory()
        if asyncio.iscoroutine(result):
            result = await result

        await self.set(key, result, ttl)
        return result  # type: ignore[return-value]

    async def clear_prefix(self, prefix: str) -> None:
        r = await self._get_redis()
        if r:
            try:
                keys = await r.keys(f"{prefix}*")
                if keys:
                    await r.delete(*keys)
            except Exception:
                pass
        self._local.clear_prefix(prefix)

    async def ping(self) -> bool:
        """Health check — returns True if Redis is reachable."""
        r = await self._get_redis()
        if r:
            try:
                return await r.ping()
            except Exception:
                return False
        return False  # in-process only, no external dep


def make_cache_key(prefix: str, **kwargs: Any) -> str:
    """Deterministic cache key from keyword arguments."""
    raw = json.dumps(kwargs, sort_keys=True, default=str)
    digest = hashlib.md5(raw.encode()).hexdigest()
    return f"{prefix}:{digest}"
