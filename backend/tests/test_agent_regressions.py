"""Regression tests for bugs that stopped real research runs.

They stub the LLM, so they run without API keys.
"""
import asyncio

import tiktoken

from agents.critic import CriticAgent, ReviewFeedback
from agents.writer import WriterAgent
from schemas.agents import AgentRole
from schemas.research import ResearchReport
from services.llm_service import LLMService


class StubLLM:
    """Records the messages it receives and returns a fixed structured result."""

    def __init__(self, result):
        self.result = result
        self.messages = None
        self.total_tokens_used = 0

    async def generate_structured(self, messages, output_schema):
        self.messages = messages
        return self.result


def test_token_estimate_accepts_dict_messages():
    # Agents send {"role", "content"} dicts; this used to raise AttributeError on msg.content.
    svc = LLMService.__new__(LLMService)
    svc._encoding = tiktoken.get_encoding("cl100k_base")
    n = svc._estimate_message_tokens(
        [{"role": "system", "content": "You are a planner."}, {"role": "user", "content": "Plan this."}]
    )
    assert n > 0


def _critic(review):
    return CriticAgent(AgentRole.CRITIC, StubLLM(review), {}, None)


def _state():
    return {
        "draft_report": {"title": "T", "abstract": "A", "sections": []},
        "findings": [{"sources": [{"url": "https://example.com/a", "title": "Source A", "snippet": "fact"}]}],
    }


def test_critic_approval_follows_score_not_model_flag():
    review = ReviewFeedback(quality_score=8, specific_revisions_requested="", approved=False)
    out = asyncio.run(_critic(review).execute(_state()))
    assert out["approved"] is True


def test_critic_rejects_when_hallucinations_found():
    review = ReviewFeedback(
        quality_score=9, hallucinations_detected=["claim X"], specific_revisions_requested="fix X", approved=True
    )
    out = asyncio.run(_critic(review).execute(_state()))
    assert out["approved"] is False


def test_critic_sees_the_sources():
    critic = _critic(ReviewFeedback(quality_score=7, specific_revisions_requested="", approved=True))
    asyncio.run(critic.execute(_state()))
    assert "https://example.com/a" in critic.llm.messages[1]["content"]


def test_writer_receives_critic_feedback():
    # The Writer used to read review["feedback"], a key the Critic never sets.
    llm = StubLLM(ResearchReport(title="T", abstract="A"))
    writer = WriterAgent(AgentRole.WRITER, llm, {}, None)
    state = {
        "query": "q",
        "analysis": {"core_narrative": "n"},
        "findings": [],
        "review": {"specific_revisions_requested": "Add a section on costs", "citation_issues": ["[2] missing"]},
    }
    asyncio.run(writer.execute(state))
    prompt = llm.messages[1]["content"]
    assert "Add a section on costs" in prompt
    assert "[2] missing" in prompt


def test_daily_quota_errors_are_not_retried():
    from services.llm_service import _is_retryable

    daily = Exception("429 RESOURCE_EXHAUSTED quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier")
    assert _is_retryable(daily) is False
    assert _is_retryable(Exception("503 UNAVAILABLE")) is True


def test_draft_report_is_json_serialisable():
    # The reports table stores JSON; datetimes in the draft made every final save fail.
    import json

    llm = StubLLM(ResearchReport(title="T", abstract="A"))
    writer = WriterAgent(AgentRole.WRITER, llm, {}, None)
    state = {"query": "q", "analysis": {"core_narrative": "n"}, "findings": [
        {"sources": [{"url": "https://example.com", "title": "E", "snippet": "s"}]}]}
    out = asyncio.run(writer.execute(state))
    json.dumps(out["draft_report"])


def test_gate_node_does_not_double_counters():
    from orchestration.graph import build_research_graph
    from orchestration.state import ResearchState

    graph = build_research_graph()
    node = graph.nodes["human_check_node"]
    out = asyncio.run(node.bound.ainvoke({"revision_count": 1, "findings": [{"a": 1}]}))
    assert not out


def test_orchestrator_handles_empty_node_updates():
    """A full graph run with stub agents must finish and return the report."""
    from types import SimpleNamespace

    from orchestration import graph as g
    from orchestration.nodes import set_agents
    from schemas.research import ResearchTask

    class Agent:
        def __init__(self, out):
            self.out = out

        async def execute(self, state):
            return self.out

    report = {"title": "T", "abstract": "A", "sections": []}
    set_agents(
        Agent({"plan": {"sub_tasks": []}}),
        Agent({"findings": [{"topic": "x"}]}),
        Agent({"analysis": {"core_narrative": "n"}}),
        Agent({"draft_report": report}),
        Agent({"review": {"quality_score": 9}, "approved": True}),
    )

    class Memory:
        async def save_state(self, task_id, update):
            assert update, "empty updates should not be saved"

    class DB:
        async def save_report(self, task_id, draft):
            self.saved = draft

    orch = g.ResearchOrchestrator.__new__(g.ResearchOrchestrator)
    orch.graph, orch.memory, orch.db = g.build_research_graph(), Memory(), DB()
    task = ResearchTask(query="test query", require_human_approval=False)
    result = asyncio.run(orch.run(task, "t1"))
    assert result.title == "T"
    state = orch.graph.get_state({"configurable": {"thread_id": "t1"}}).values
    assert state["revision_count"] == 1
    assert len(state["findings"]) == 1
