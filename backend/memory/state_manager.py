"""State management across agents using Redis (fast) + PostgreSQL (durable)."""

from __future__ import annotations

import json
from typing import Any, Optional

import structlog

from services.cache_service import CacheService
from services.db_service import DatabaseService

logger = structlog.get_logger(__name__)


class StateManager:
    """Manages per-task research state.

    - **Redis** is the primary read/write store for hot state (fast agent
      hand-offs).
    - **PostgreSQL** is the durable backing store updated on every write so
      that state survives process restarts.

    State keys include: ``current_agent``, ``findings``, ``draft_sections``,
    ``revision_count``, ``token_budget``, and arbitrary user-defined keys.
    """

    _KEY_PREFIX = "state:"

    def __init__(
        self,
        cache: CacheService,
        db: DatabaseService,
    ) -> None:
        self._cache = cache
        self._db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def save_state(self, task_id: str, state_dict: dict[str, Any]) -> None:
        """Persist the entire *state_dict* for *task_id*."""
        key = self._redis_key(task_id)
        serialised = json.dumps(state_dict, default=str)

        # Write to Redis
        await self._cache.set(key, serialised, ttl=7200)  # 2-hour TTL

        # Write durable copy to Postgres via the task record
        status = state_dict.get("status", "unknown")
        progress = state_dict.get("progress_pct", 0.0)
        current_agent = state_dict.get("current_agent")
        token_usage = state_dict.get("token_usage", {})
        await self._db.update_task_status(
            task_id=task_id,
            status=status,
            progress=progress,
            current_agent=current_agent,
            token_usage=token_usage,
        )

        logger.debug("state_saved", task_id=task_id, keys=list(state_dict.keys()))

    async def load_state(self, task_id: str) -> dict[str, Any]:
        """Load state for *task_id*.

        Tries Redis first; falls back to reconstructing from Postgres.
        """
        key = self._redis_key(task_id)
        raw = await self._cache.get(key)
        if raw is not None:
            logger.debug("state_loaded_from_redis", task_id=task_id)
            return json.loads(raw)

        # Fallback to DB
        task_row = await self._db.get_task(task_id)
        if task_row is not None:
            logger.info("state_loaded_from_db", task_id=task_id)
            state: dict[str, Any] = {
                "task_id": task_row["task_id"],
                "query": task_row["query"],
                "status": task_row["status"],
                "current_agent": task_row.get("current_agent"),
                "progress_pct": task_row.get("progress_pct", 0.0),
                "token_usage": task_row.get("token_usage", {}),
                "findings": [],
                "draft_sections": [],
                "revision_count": 0,
                "token_budget": 100_000,
            }
            # Re-hydrate Redis
            await self._cache.set(
                key, json.dumps(state, default=str), ttl=7200
            )
            return state

        logger.warning("state_not_found", task_id=task_id)
        return {}

    async def update_state(
        self,
        task_id: str,
        key: str,
        value: Any,
    ) -> None:
        """Update a single *key* in the task state."""
        state = await self.load_state(task_id)
        state[key] = value
        await self.save_state(task_id, state)
        logger.debug("state_key_updated", task_id=task_id, key=key)

    async def get_state_value(
        self,
        task_id: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """Return a single value from the task state."""
        state = await self.load_state(task_id)
        return state.get(key, default)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _redis_key(self, task_id: str) -> str:
        return f"{self._KEY_PREFIX}{task_id}"
