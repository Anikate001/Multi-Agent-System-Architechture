"""Application settings with Pydantic BaseSettings for environment-driven configuration."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment variables and .env file.

    All settings can be overridden via environment variables (case-insensitive).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- API Keys -----------------------------------------------------------
    gemini_api_key: str = Field(
        ...,
        description="Google Gemini API key for LLM access",
    )
    tavily_api_key: str = Field(
        ...,
        description="Tavily API key for web search",
    )
    langsmith_api_key: Optional[str] = Field(
        default=None,
        description="Optional LangSmith API key for tracing",
    )

    # --- Infrastructure ------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@db:5432/nexus",
        description="Async PostgreSQL connection string",
    )
    redis_url: str = Field(
        default="redis://redis:6379/0",
        description="Redis connection string for caching and state",
    )

    # --- Observability -------------------------------------------------------
    langsmith_project: str = Field(
        default="nexus-research",
        description="LangSmith project name for tracing",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # --- LLM Defaults --------------------------------------------------------
    model_name: str = Field(
        default="gemini-3.5-flash-lite",
        description="Default Gemini model to use",
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Default sampling temperature",
    )

    # --- Rate / Budget Limits ------------------------------------------------
    max_tokens_per_request: int = Field(
        default=100_000,
        gt=0,
        description="Maximum token budget per single research run",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts for transient failures",
    )
    rate_limit_rpm: int = Field(
        default=60,
        gt=0,
        description="Rate limit: requests per minute to upstream LLM",
    )

    # --- Validators ----------------------------------------------------------
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got '{v}'")
        return upper

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
            raise ValueError(
                "database_url must use the 'postgresql+asyncpg://' or "
                "'sqlite+aiosqlite://' scheme for async support"
            )
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, singleton Settings instance.

    Using ``lru_cache`` guarantees we parse environment / .env exactly once
    across the process lifetime while still allowing tests to override via
    ``get_settings.cache_clear()``.
    """
    return Settings()  # type: ignore[call-arg]
