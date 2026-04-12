"""
LangGraph Workflow Definition — The brain of the multi-agent system.

Builds a StateGraph that connects all agents with:
- Conditional routing (planner decides the path)
- Feedback loops (reviewer can send work back)
- Revision guards (max retry limit)
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import AgentState
from agents.planner import planner_agent
from agents.researcher import researcher_agent
from agents.coder import coder_agent
from agents.reviewer import reviewer_agent
from agents.aggregator import aggregator_agent


# ═══════════════════════════════════════════════════════════════════════
#  ROUTING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def route_after_planner(state: dict) -> Literal["researcher", "coder", "reviewer"]:
    """
    Decide where to go after the Planner based on the route it chose.

    Routes:
    - researcher           → go to researcher (then reviewer)
    - coder                → go to coder (then reviewer)
    - researcher_then_coder → go to researcher first
    - direct_review        → skip specialists, go straight to reviewer
    """
    route = state.get("next_agent", "direct_review")

    if route in ("researcher", "researcher_then_coder"):
        return "researcher"
    elif route == "coder":
        return "coder"
    else:
        # direct_review or unknown → go to reviewer
        return "reviewer"


def route_after_researcher(state: dict) -> Literal["coder", "reviewer"]:
    """
    After research, decide if we also need to code.
    """
    route = state.get("next_agent", "")

    if route == "researcher_then_coder":
        return "coder"
    else:
        return "reviewer"


def route_after_reviewer(state: dict) -> Literal["coder", "researcher", "aggregator"]:
    """
    After review, decide if we pass to aggregator or loop back.
    """
    next_agent = state.get("next_agent", "aggregator")

    if next_agent == "coder":
        return "coder"
    elif next_agent == "researcher":
        return "researcher"
    else:
        return "aggregator"


# ═══════════════════════════════════════════════════════════════════════
#  GRAPH BUILDER
# ═══════════════════════════════════════════════════════════════════════

def build_graph(use_memory: bool = True):
    """
    Build and compile the multi-agent workflow graph.

    Graph topology:
        START → planner
        planner → [researcher | coder | reviewer]  (conditional)
        researcher → [coder | reviewer]             (conditional)
        coder → reviewer
        reviewer → [aggregator | coder | researcher] (conditional — feedback loop)
        aggregator → END

    Args:
        use_memory: If True, enables MemorySaver for state persistence.

    Returns:
        Compiled LangGraph application.
    """
    # ── Create the graph ────────────────────────────────────────────
    graph = StateGraph(AgentState)

    # ── Add all agent nodes ─────────────────────────────────────────
    graph.add_node("planner", planner_agent)
    graph.add_node("researcher", researcher_agent)
    graph.add_node("coder", coder_agent)
    graph.add_node("reviewer", reviewer_agent)
    graph.add_node("aggregator", aggregator_agent)

    # ── Entry point ─────────────────────────────────────────────────
    graph.add_edge(START, "planner")

    # ── Planner → conditional routing ───────────────────────────────
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "researcher": "researcher",
            "coder": "coder",
            "reviewer": "reviewer",
        },
    )

    # ── Researcher → conditional (code or review) ───────────────────
    graph.add_conditional_edges(
        "researcher",
        route_after_researcher,
        {
            "coder": "coder",
            "reviewer": "reviewer",
        },
    )

    # ── Coder → always goes to reviewer ─────────────────────────────
    graph.add_edge("coder", "reviewer")

    # ── Reviewer → conditional (pass/fail loop) ─────────────────────
    graph.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {
            "coder": "coder",
            "researcher": "researcher",
            "aggregator": "aggregator",
        },
    )

    # ── Aggregator → END ────────────────────────────────────────────
    graph.add_edge("aggregator", END)

    # ── Compile ─────────────────────────────────────────────────────
    if use_memory:
        memory = MemorySaver()
        return graph.compile(checkpointer=memory)
    else:
        return graph.compile()


# ── Quick access ────────────────────────────────────────────────────
def get_app(use_memory: bool = True):
    """Get a compiled graph app instance."""
    return build_graph(use_memory=use_memory)
