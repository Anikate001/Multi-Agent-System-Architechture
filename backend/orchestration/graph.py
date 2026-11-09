import structlog
from typing import Dict, Any, Callable, Awaitable
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from orchestration.state import ResearchState
from orchestration.nodes import (
    plan_node, research_node, analyze_node, write_node,
    review_node, human_review_node,
    should_revise, needs_human_approval, handle_human_decision,
    set_agents
)
from schemas.research import ResearchTask, ResearchReport
from schemas.agents import AgentRole
from agents.planner import PlannerAgent
from agents.researcher import ResearchAgent
from agents.analyst import AnalystAgent
from agents.writer import WriterAgent
from agents.critic import CriticAgent
from services.llm_service import LLMService
from tools.web_search import WebSearchTool
from memory.state_manager import StateManager

logger = structlog.get_logger(__name__)


def build_research_graph():
    """Constructs the multi-agent LangGraph state machine."""
    workflow = StateGraph(ResearchState)

    # --- Nodes ---
    workflow.add_node("plan", plan_node)
    workflow.add_node("research", research_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("write", write_node)
    workflow.add_node("review", review_node)
    workflow.add_node("human_review", human_review_node)

    # Pass-through node to chain two conditional edges cleanly
    async def _passthrough(state):
        # Return no updates. Returning the whole state would re-apply the additive
        # reducers, doubling revision_count and duplicating findings and errors.
        return {}

    workflow.add_node("human_check_node", _passthrough)

    # --- Edges ---
    workflow.add_edge(START, "plan")
    workflow.add_edge("plan", "research")
    workflow.add_edge("research", "analyze")
    workflow.add_edge("analyze", "write")
    workflow.add_edge("write", "review")

    # After review: revise or move to human-check gate
    workflow.add_conditional_edges(
        "review",
        should_revise,
        {
            "revise": "write",
            "approve": "human_check_node",
        },
    )

    # After human-check gate: human review or complete
    workflow.add_conditional_edges(
        "human_check_node",
        needs_human_approval,
        {
            "human_review": "human_review",
            "complete": END,
        },
    )

    # After human review: accept or send back for revision
    workflow.add_conditional_edges(
        "human_review",
        handle_human_decision,
        {
            "complete": END,
            "revise": "write",
        },
    )

    # Compile with in-memory checkpointer for pause/resume
    checkpointer = MemorySaver()
    # Pause before human_review so the API can wait for approve/reject; without this the
    # graph would run straight through human_review and loop back to the writer.
    return workflow.compile(checkpointer=checkpointer, interrupt_before=["human_review"])


class ResearchOrchestrator:
    """Manages the execution of the multi-agent research graph."""

    def __init__(self, settings, db_service, cache_service):
        self.settings = settings
        self.db = db_service
        self.memory = StateManager(cache_service, db_service)

        # Initialize LLM service
        self.llm = LLMService(settings)
        self.tools = {
            "web_search": WebSearchTool(settings.tavily_api_key, cache_service)
        }

        # Instantiate agents
        planner = PlannerAgent(AgentRole.PLANNER, self.llm, self.tools, self.memory)
        researcher = ResearchAgent(AgentRole.RESEARCHER, self.llm, self.tools, self.memory)
        analyst = AnalystAgent(AgentRole.ANALYST, self.llm, self.tools, self.memory)
        writer = WriterAgent(AgentRole.WRITER, self.llm, self.tools, self.memory)
        critic = CriticAgent(AgentRole.CRITIC, self.llm, self.tools, self.memory)

        # Register agents in the node registry
        set_agents(planner, researcher, analyst, writer, critic)

        self.graph = build_research_graph()

    async def run(
        self,
        task: ResearchTask,
        task_id: str,
        callback: Callable[[Dict], Awaitable[None]] = None,
    ) -> ResearchReport:
        """Run the complete research workflow."""
        logger.info("starting_orchestration", task_id=task_id)

        initial_state = {
            "task_id": task_id,
            "query": task.query,
            "depth": task.depth,
            "require_human_approval": task.require_human_approval,
            "plan": None,
            "findings": [],
            "analysis": None,
            "draft_report": None,
            "review": None,
            "revision_count": 0,
            "approved": False,
            "human_approved": None,
            "agent_actions": [],
            "token_usage": {},
            "errors": [],
            "status": "STARTING",
            "current_agent": "SYSTEM",
        }

        config = {"configurable": {"thread_id": task_id}}

        async for output in self.graph.astream(initial_state, config=config):
            node_name = list(output.keys())[0]
            # Pass-through and interrupt steps yield no update (None or {}).
            state_update = output[node_name] or {}

            logger.info("graph_step_completed", node=node_name)

            if state_update:
                await self.memory.save_state(task_id, state_update)

            if callback:
                await callback(
                    {
                        "task_id": task_id,
                        "node": node_name,
                        "status": state_update.get("status"),
                        "current_agent": state_update.get("current_agent"),
                    }
                )

        # Retrieve final state
        final_state = self.graph.get_state(config).values

        draft = final_state.get("draft_report")
        if draft:
            report = ResearchReport(**draft)
            await self.db.save_report(task_id, draft)
            return report
        else:
            raise ValueError("Workflow completed but no report was generated.")

    async def get_state(self, task_id: str) -> Dict[str, Any]:
        """Retrieve current graph state."""
        config = {"configurable": {"thread_id": task_id}}
        try:
            state = self.graph.get_state(config)
            return state.values
        except Exception:
            return await self.memory.load_state(task_id)

    async def approve_task(self, task_id: str) -> None:
        """Provide human approval to resume the graph."""
        config = {"configurable": {"thread_id": task_id}}
        self.graph.update_state(
            config, {"human_approved": True, "status": "APPROVED_BY_HUMAN"}
        )
        async for _ in self.graph.astream(None, config=config):
            pass

    async def reject_task(self, task_id: str, feedback: str) -> None:
        """Provide human rejection to trigger revision."""
        config = {"configurable": {"thread_id": task_id}}
        current_state = self.graph.get_state(config).values
        review = current_state.get("review", {})
        review["specific_revisions_requested"] = feedback

        self.graph.update_state(
            config,
            {
                "human_approved": False,
                "status": "REJECTED_BY_HUMAN",
                "review": review,
            },
        )
        async for _ in self.graph.astream(None, config=config):
            pass
