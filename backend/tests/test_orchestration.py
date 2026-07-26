import pytest
from backend.orchestration.graph import build_research_graph
from backend.orchestration.state import ResearchState

def test_graph_compilation():
    graph = build_research_graph()
    assert graph is not None

def test_initial_state():
    state = ResearchState(
        task_id="test",
        query="test query",
        depth="standard",
        require_human_approval=False,
        plan=None,
        findings=[],
        analysis=None,
        draft_report=None,
        review=None,
        revision_count=0,
        approved=False,
        human_approved=None,
        agent_actions=[],
        token_usage={},
        errors=[],
        status="STARTING",
        current_agent="SYSTEM"
    )
    assert state["task_id"] == "test"
