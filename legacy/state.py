"""
State schema for the Multi-Agent System.
Defines the shared memory structure that flows between all agents.

Uses LangGraph's Annotated reducers for intelligent state merging:
- `add_messages` → smart message history (dedup by ID, supports updates)
- Default fields → overwrite on update
"""

from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Shared state that flows through the entire agent graph.

    Every agent reads from this state and returns a partial dict
    with only the keys it wants to update.
    """

    # ── Conversation History ────────────────────────────────────────
    # Uses add_messages reducer: appends new messages, deduplicates by ID
    messages: Annotated[list[AnyMessage], add_messages]

    # ── User Input ──────────────────────────────────────────────────
    task: str                   # The original user request

    # ── Agent Outputs ───────────────────────────────────────────────
    plan: str                   # Planner's structured plan
    research: str               # Researcher's findings
    code: str                   # Coder's generated code
    review: str                 # Reviewer's feedback
    final_output: str           # Aggregator's polished response

    # ── Control Flow ────────────────────────────────────────────────
    next_agent: str             # Routing target (set by planner/reviewer)
    revision_count: int         # Feedback loop counter (max = MAX_REVISIONS)
