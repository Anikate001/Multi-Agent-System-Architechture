"""Redis-backed caching service with TTL, pattern invalidation, and
compute-on-miss semantics."""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Optional

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger(__name__)


class CacheService:
    """Thin async wrapper around Redis providing cache primitives.

    All values are stored as JSON-encoded strings so that complex objects
    can be cached transparently.
    """

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._redis: Optional[Redis] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Establish the Redis connection pool."""
        if self._redis is None:
            self._redis = Redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            logger.info("cache_connected", redis_url=self._redis_url)

    async def disconnect(self) -> None:
        """Gracefully close the Redis connection pool."""
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
            logger.info("cache_disconnected")

    def _ensure_connected(self) -> Redis:
        if self._redis is None:
            raise RuntimeError(
                "CacheService is not connected. Call `await connect()` first."
            )
        return self._redis

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Optional[str]:
        """Return the cached value for *key*, or ``None`` on cache miss."""
        redis = self._ensure_connected()
        try:
            value = await redis.get(key)
            if value is not None:
                logger.debug("cache_hit", key=key)
            else:
                logger.debug("cache_miss", key=key)
            return value
        except Exception:
            logger.exception("cache_get_error", key=key)
            return None

    async def set(self, key: str, value: str, ttl: int = 3600) -> None:
        """Store *value* under *key* with a TTL in seconds."""
        redis = self._ensure_connected()
        try:
            await redis.set(key, value, ex=ttl)
            logger.debug("cache_set", key=key, ttl=ttl)
        except Exception:
            logger.exception("cache_set_error", key=key)

    async def get_json(self, key: str) -> Optional[Any]:
        """Return the cached value deserialised from JSON."""
        raw = await self.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Serialise *value* as JSON and cache it."""
        await self.set(key, json.dumps(value, default=str), ttl=ttl)

    async def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Awaitable[str]],
        ttl: int = 3600,
    ) -> str:
        """Return cached value or call *compute_fn*, cache the result, and
        return it.  This is the standard cache-aside pattern.
        """
        cached = await self.get(key)
        if cached is not None:
            return cached
        computed = await compute_fn()
        await self.set(key, computed, ttl=ttl)
        return computed

    async def invalidate(self, pattern: str) -> int:
        """Delete all keys matching the glob *pattern*.

        Returns the number of keys deleted.
        """
        redis = self._ensure_connected()
        try:
            keys: list[str] = []
            async for key in redis.scan_iter(match=pattern, count=200):
                keys.append(key)
            if keys:
                deleted = await redis.delete(*keys)
                logger.info("cache_invalidated", pattern=pattern, count=deleted)
                return int(deleted)
            return 0
        except Exception:
            logger.exception("cache_invalidate_error", pattern=pattern)
            return 0

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Return ``True`` if Redis is reachable."""
        try:
            redis = self._ensure_connected()
            pong = await redis.ping()
            return bool(pong)
        except Exception:
            logger.warning("cache_health_check_failed")
            return False
