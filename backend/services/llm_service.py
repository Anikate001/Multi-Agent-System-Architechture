"""LLM service wrapping Google Gemini via LangChain, with rate-limiting,
retries, token tracking, and structured-output support."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional, Type

import structlog
import tiktoken
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import Settings

logger = structlog.get_logger(__name__)

# Approximate cost per 1M tokens (Gemini 2.0 Flash pricing — adjust as needed)
_INPUT_COST_PER_M = 0.10
_OUTPUT_COST_PER_M = 0.40


class LLMService:
    """Manages all interactions with the Google Gemini LLM.

    Features:
    - Automatic retry with exponential back-off on transient errors.
    - Per-minute rate-limiting via ``asyncio.Semaphore``.
    - Cumulative token & cost tracking.
    - Optional structured (Pydantic) output parsing.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._llm = ChatGoogleGenerativeAI(
            model=settings.model_name,
            google_api_key=settings.gemini_api_key,
            temperature=settings.temperature,
            max_retries=settings.max_retries,
        )
        self._semaphore = asyncio.Semaphore(settings.rate_limit_rpm)
        self._encoding = tiktoken.get_encoding("cl100k_base")

        # Tracking
        self.total_tokens_used: int = 0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_cost: float = 0.0
        self.request_count: int = 0

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------

    def count_tokens(self, text: str) -> int:
        """Return an approximate token count for *text*."""
        return len(self._encoding.encode(text))

    def _estimate_message_tokens(self, messages: list[BaseMessage]) -> int:
        total = 0
        for msg in messages:
            total += self.count_tokens(msg.content if isinstance(msg.content, str) else str(msg.content))
        return total

    # ------------------------------------------------------------------
    # Core generation
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def generate(
        self,
        messages: list[BaseMessage],
        structured_output: Optional[Type[BaseModel]] = None,
        temperature: Optional[float] = None,
    ) -> str | BaseModel:
        """Send *messages* to Gemini and return the response text or a parsed
        Pydantic model if *structured_output* is provided.

        Parameters
        ----------
        messages:
            LangChain message objects (SystemMessage, HumanMessage, etc.).
        structured_output:
            If given, the LLM output is parsed into this Pydantic schema via
            LangChain's ``with_structured_output`` mechanism.
        temperature:
            Override the default temperature for this call.
        """
        async with self._semaphore:
            start = time.perf_counter()
            input_tokens = self._estimate_message_tokens(messages)

            llm = self._llm
            if temperature is not None:
                llm = self._llm.bind(temperature=temperature)

            if structured_output is not None:
                llm_with_schema = llm.with_structured_output(structured_output)
                result = await llm_with_schema.ainvoke(messages)
            else:
                ai_message = await llm.ainvoke(messages)
                result = ai_message.content

            latency_ms = (time.perf_counter() - start) * 1000
            output_text = result if isinstance(result, str) else result.model_dump_json()
            output_tokens = self.count_tokens(output_text)

            # Update tracking
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_tokens_used += input_tokens + output_tokens
            self.total_cost += (
                input_tokens / 1_000_000 * _INPUT_COST_PER_M
                + output_tokens / 1_000_000 * _OUTPUT_COST_PER_M
            )
            self.request_count += 1

            logger.info(
                "llm_generate",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=round(latency_ms, 1),
                structured=structured_output is not None,
                request_count=self.request_count,
            )

            return result

    async def generate_structured(
        self,
        messages: list[BaseMessage],
        output_schema: Type[BaseModel],
    ) -> BaseModel:
        """Convenience wrapper that always returns a validated Pydantic model."""
        result = await self.generate(messages, structured_output=output_schema)
        if not isinstance(result, BaseModel):
            raise TypeError(
                f"Expected Pydantic model, got {type(result).__name__}"
            )
        return result

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def get_metrics(self) -> dict[str, Any]:
        """Return a snapshot of cumulative usage metrics."""
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "request_count": self.request_count,
        }
