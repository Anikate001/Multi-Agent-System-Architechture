"""Web search tool backed by the Tavily Search API with caching and retries."""

from __future__ import annotations

import asyncio
import hashlib
import time
from datetime import datetime, timezone
from typing import Optional

import structlog
from tavily import AsyncTavilyClient
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from schemas.research import Source
from services.cache_service import CacheService

logger = structlog.get_logger(__name__)


class WebSearchTool:
    """Performs web searches via Tavily, caches results, and returns typed
    :class:`Source` objects."""

    def __init__(
        self,
        api_key: str,
        cache: Optional[CacheService] = None,
        rate_limit_rpm: int = 60,
    ) -> None:
        self._client = AsyncTavilyClient(api_key=api_key)
        self._cache = cache
        self._semaphore = asyncio.Semaphore(rate_limit_rpm)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        reraise=True,
    )
    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
    ) -> list[Source]:
        """Search the web for *query* and return up to *max_results* sources.

        Parameters
        ----------
        query:
            The search string.
        max_results:
            Maximum number of sources to return.
        search_depth:
            Tavily search depth — ``"basic"`` or ``"advanced"``.
        """
        cache_key = self._cache_key(query, max_results, search_depth)

        # Try cache first
        if self._cache is not None:
            cached = await self._cache.get_json(cache_key)
            if cached is not None:
                logger.info("web_search_cache_hit", query=query)
                return [Source(**s) for s in cached]

        # Call Tavily
        async with self._semaphore:
            start = time.perf_counter()
            try:
                response = await self._client.search(
                    query=query,
                    max_results=max_results,
                    search_depth=search_depth,
                )
            except Exception:
                logger.exception("web_search_failed", query=query)
                raise
            latency_ms = (time.perf_counter() - start) * 1000

        results: list[Source] = []
        for item in response.get("results", []):
            results.append(
                Source(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    snippet=item.get("content", "")[:500],
                    relevance_score=item.get("score", 0.0),
                    retrieved_at=datetime.now(timezone.utc),
                )
            )

        logger.info(
            "web_search_completed",
            query=query,
            results=len(results),
            latency_ms=round(latency_ms, 1),
        )

        # Cache results
        if self._cache is not None and results:
            await self._cache.set_json(
                cache_key,
                [s.model_dump(mode="json") for s in results],
                ttl=3600,
            )

        return results

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _cache_key(query: str, max_results: int, depth: str) -> str:
        h = hashlib.sha256(f"{query}|{max_results}|{depth}".encode()).hexdigest()[:16]
        return f"websearch:{h}"
