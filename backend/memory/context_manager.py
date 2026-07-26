"""Context window management — compression, pruning, and relevance retrieval."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Callable, Optional

import structlog
import tiktoken
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

logger = structlog.get_logger(__name__)


class ContextManager:
    """Utilities for keeping the LLM context window within budget.

    Responsibilities:
    - Count tokens accurately.
    - Compress older messages into concise summaries.
    - Prune low-priority messages.
    - Retrieve the most query-relevant findings from an accumulating pool.
    """

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        self._enc = tiktoken.get_encoding(encoding_name)

    # ------------------------------------------------------------------
    # Token counting
    # ------------------------------------------------------------------

    def count_tokens(self, text: str) -> int:
        return len(self._enc.encode(text))

    def count_messages_tokens(self, messages: list[BaseMessage]) -> int:
        total = 0
        for msg in messages:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            total += self.count_tokens(content) + 4  # per-message overhead
        return total

    # ------------------------------------------------------------------
    # Compress
    # ------------------------------------------------------------------

    async def compress_context(
        self,
        messages: list[BaseMessage],
        max_tokens: int = 8000,
    ) -> list[BaseMessage]:
        """Summarise older messages so the total stays under *max_tokens*.

        The most recent messages are preserved verbatim; earlier ones are
        collapsed into a single summary message.
        """
        if not messages:
            return messages

        total = self.count_messages_tokens(messages)
        if total <= max_tokens:
            return messages

        # Keep the system message + the latest N messages that fit
        system_msgs: list[BaseMessage] = []
        other_msgs: list[BaseMessage] = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_msgs.append(msg)
            else:
                other_msgs.append(msg)

        # Walk backwards through other_msgs keeping those that fit
        kept: list[BaseMessage] = []
        budget = max_tokens - self.count_messages_tokens(system_msgs) - 200  # 200 for summary msg
        for msg in reversed(other_msgs):
            msg_tokens = self.count_tokens(
                msg.content if isinstance(msg.content, str) else str(msg.content)
            ) + 4
            if budget - msg_tokens >= 0:
                kept.insert(0, msg)
                budget -= msg_tokens
            else:
                break

        # Summarise the dropped messages
        dropped = other_msgs[: len(other_msgs) - len(kept)]
        if dropped:
            summary_text = self._build_summary(dropped)
            summary_msg = HumanMessage(
                content=f"[Compressed context summary]\n{summary_text}"
            )
            result = system_msgs + [summary_msg] + kept
        else:
            result = system_msgs + kept

        logger.info(
            "context_compressed",
            original_msgs=len(messages),
            result_msgs=len(result),
            original_tokens=total,
            result_tokens=self.count_messages_tokens(result),
        )
        return result

    # ------------------------------------------------------------------
    # Prune
    # ------------------------------------------------------------------

    async def prune_context(
        self,
        messages: list[BaseMessage],
        priority_fn: Callable[[BaseMessage], float],
    ) -> list[BaseMessage]:
        """Remove the lowest-priority messages according to *priority_fn*.

        *priority_fn* should return a float (higher = more important).
        The bottom 30% are dropped.
        """
        if len(messages) <= 3:
            return messages

        scored = [(priority_fn(m), m) for m in messages]
        scored.sort(key=lambda x: x[0], reverse=True)

        keep_count = max(3, int(len(scored) * 0.7))
        kept = [m for _, m in scored[:keep_count]]

        # Restore original order
        order_map = {id(m): i for i, m in enumerate(messages)}
        kept.sort(key=lambda m: order_map.get(id(m), 0))

        logger.info(
            "context_pruned",
            original=len(messages),
            kept=len(kept),
        )
        return kept

    # ------------------------------------------------------------------
    # Relevance retrieval
    # ------------------------------------------------------------------

    async def get_relevant_context(
        self,
        query: str,
        all_findings: list[dict[str, Any]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Return the *top_k* findings most relevant to *query* using
        simple textual similarity."""
        if not all_findings:
            return []

        scored: list[tuple[float, dict[str, Any]]] = []
        query_lower = query.lower()
        for finding in all_findings:
            text = (
                finding.get("topic", "")
                + " "
                + finding.get("summary", "")
                + " "
                + " ".join(finding.get("key_points", []))
            ).lower()
            sim = SequenceMatcher(None, query_lower, text).ratio()
            scored.append((sim, finding))

        scored.sort(key=lambda x: x[0], reverse=True)
        relevant = [f for _, f in scored[:top_k]]

        logger.info(
            "relevant_context_retrieved",
            query_len=len(query),
            total_findings=len(all_findings),
            returned=len(relevant),
        )
        return relevant

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(messages: list[BaseMessage]) -> str:
        """Build a brief textual summary of *messages*."""
        parts: list[str] = []
        for msg in messages:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            # Take the first 120 chars of each message
            preview = content[:120].replace("\n", " ").strip()
            role = msg.type if hasattr(msg, "type") else "unknown"
            parts.append(f"- [{role}] {preview}")
        return "\n".join(parts)
