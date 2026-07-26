"""Pydantic models for agent communication, actions, and workflow status."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Roles that an agent can assume within the research workflow."""

    PLANNER = "planner"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    CRITIC = "critic"
    TOOL_EXECUTOR = "tool_executor"


class AgentAction(BaseModel):
    """Record of a single action taken by an agent."""

    agent: AgentRole = Field(..., description="The agent that performed the action")
    action: str = Field(..., description="Human-readable description of the action")
    input_data: Any = Field(
        default=None,
        description="Serialisable snapshot of the input given to the agent",
    )
    output_data: Any = Field(
        default=None,
        description="Serialisable snapshot of the output produced",
    )
    tokens_used: int = Field(
        default=0,
        ge=0,
        description="Number of tokens consumed by this action",
    )
    latency_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Wall-clock latency in milliseconds",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the action occurred",
    )
    success: bool = Field(
        default=True,
        description="Whether the action completed successfully",
    )


class AgentMessage(BaseModel):
    """A message exchanged between agents in the workflow."""

    from_agent: AgentRole = Field(..., description="Sending agent")
    to_agent: AgentRole = Field(..., description="Receiving agent")
    content: Any = Field(..., description="Message payload (string or structured data)")
    message_type: Literal["task", "result", "feedback", "revision"] = Field(
        ...,
        description="Semantic type of the message",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional key-value metadata",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the message was created",
    )


class WorkflowStatus(str, Enum):
    """High-level states the research workflow can be in."""

    PLANNING = "planning"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    WRITING = "writing"
    REVIEWING = "reviewing"
    REVISING = "revising"
    HUMAN_REVIEW = "human_review"
    COMPLETED = "completed"
    FAILED = "failed"
