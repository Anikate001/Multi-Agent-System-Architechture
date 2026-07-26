"""Pydantic models for HTTP and WebSocket API contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from schemas.agents import AgentAction
from schemas.research import ResearchReport


# ---------------------------------------------------------------------------
# REST request / response models
# ---------------------------------------------------------------------------

class ResearchRequest(BaseModel):
    """Body for POST /api/research — starts a new research task."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The research question to investigate",
    )
    depth: Literal["quick", "standard", "deep"] = Field(
        default="standard",
        description="Research depth",
    )
    max_sources: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Cap on the number of sources to retrieve",
    )
    require_approval: bool = Field(
        default=False,
        description="Pause for human approval before finalising",
    )


class ResearchResponse(BaseModel):
    """Acknowledgement returned when a research task is accepted."""

    task_id: str = Field(..., description="Unique identifier for the queued task")
    status: str = Field(..., description="Initial status (typically 'planning')")
    message: str = Field(
        default="Research task accepted",
        description="Human-readable status message",
    )


class TaskStatusResponse(BaseModel):
    """Detailed status of a running or completed task."""

    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Current workflow status")
    current_agent: Optional[str] = Field(
        default=None,
        description="Which agent is currently executing",
    )
    progress_pct: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Estimated percentage completion",
    )
    agent_actions: list[AgentAction] = Field(
        default_factory=list,
        description="Ordered list of agent actions taken so far",
    )
    token_usage: dict[str, int] = Field(
        default_factory=dict,
        description="Token usage broken down by agent role",
    )
    estimated_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated cost in USD",
    )
    report: Optional[ResearchReport] = Field(
        default=None,
        description="Final report (present only when status == 'completed')",
    )


class HealthResponse(BaseModel):
    """Health-check payload returned by GET /api/health."""

    status: str = Field(..., description="'healthy' or 'degraded'")
    version: str = Field(..., description="Application version string")
    uptime_seconds: float = Field(..., ge=0.0, description="Seconds since startup")
    db_connected: bool = Field(..., description="PostgreSQL reachable")
    redis_connected: bool = Field(..., description="Redis reachable")
    active_tasks: int = Field(
        default=0,
        ge=0,
        description="Number of currently running research tasks",
    )


# ---------------------------------------------------------------------------
# WebSocket message envelope
# ---------------------------------------------------------------------------

class WebSocketMessage(BaseModel):
    """Envelope for all WebSocket push messages."""

    type: Literal[
        "status",
        "agent_action",
        "report",
        "error",
        "approval_request",
    ] = Field(..., description="Discriminator for the payload type")
    data: Any = Field(..., description="Payload (shape depends on `type`)")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Server timestamp of the event",
    )
