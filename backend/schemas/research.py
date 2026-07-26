"""Pydantic domain models for research artefacts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class Source(BaseModel):
    """An external information source discovered during research."""

    url: str = Field(..., description="Full URL of the source")
    title: str = Field(..., description="Human-readable title")
    snippet: str = Field(
        default="",
        description="Short excerpt or summary from the source",
    )
    relevance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="0-1 relevance score relative to the query",
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the source was fetched",
    )


class Citation(BaseModel):
    """A single citation linking a claim to a source."""

    claim: str = Field(..., description="The claim or statement being cited")
    source_url: str = Field(..., description="URL of the supporting source")
    source_title: str = Field(..., description="Title of the supporting source")
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence that the source supports the claim",
    )
    verified: bool = Field(
        default=False,
        description="Whether a verification pass confirmed the claim",
    )


class ResearchFinding(BaseModel):
    """A cohesive finding produced by the research agent."""

    topic: str = Field(..., description="Sub-topic this finding addresses")
    summary: str = Field(..., description="Narrative summary of the finding")
    key_points: list[str] = Field(
        default_factory=list,
        description="Bullet-point key takeaways",
    )
    sources: list[Source] = Field(
        default_factory=list,
        description="Sources that contributed to this finding",
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence in this finding",
    )


class ReportSection(BaseModel):
    """A single section of the final research report."""

    title: str = Field(..., description="Section heading")
    content: str = Field(..., description="Full prose content of the section")
    citations: list[Citation] = Field(
        default_factory=list,
        description="Citations used in this section",
    )
    word_count: int = Field(
        default=0,
        ge=0,
        description="Word count of the section content",
    )


class ResearchReport(BaseModel):
    """The complete research report output."""

    title: str = Field(..., description="Report title")
    abstract: str = Field(..., description="Executive summary / abstract")
    sections: list[ReportSection] = Field(
        default_factory=list,
        description="Ordered list of report sections",
    )
    bibliography: list[Source] = Field(
        default_factory=list,
        description="Full list of referenced sources",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Arbitrary metadata (model versions, run info, etc.)",
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of report generation",
    )
    total_citations: int = Field(
        default=0,
        ge=0,
        description="Total number of citations across all sections",
    )
    quality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="Overall quality score assigned by the critic (0-10)",
    )


class ResearchTask(BaseModel):
    """Inbound task specification for a research run."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The user's research question or topic",
    )
    depth: Literal["quick", "standard", "deep"] = Field(
        default="standard",
        description="Depth of research: quick (surface), standard, or deep (exhaustive)",
    )
    max_sources: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of sources to retrieve",
    )
    include_code_analysis: bool = Field(
        default=False,
        description="Whether to enable code execution / analysis tools",
    )
    require_human_approval: bool = Field(
        default=False,
        description="If True, the workflow pauses for human review before finalising",
    )
