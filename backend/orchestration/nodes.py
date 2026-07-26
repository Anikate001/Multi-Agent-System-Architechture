from typing import Dict, Any, Literal
import structlog
from datetime import datetime

from orchestration.state import ResearchState
from agents.planner import PlannerAgent
from agents.researcher import ResearchAgent
from agents.analyst import AnalystAgent
from agents.writer import WriterAgent
from agents.critic import CriticAgent
from schemas.agents import AgentRole

logger = structlog.get_logger(__name__)

# Registry to hold instantiated agents
_AGENTS = {}

def set_agents(planner, researcher, analyst, writer, critic):
    _AGENTS[AgentRole.PLANNER.value] = planner
    _AGENTS[AgentRole.RESEARCHER.value] = researcher
    _AGENTS[AgentRole.ANALYST.value] = analyst
    _AGENTS[AgentRole.WRITER.value] = writer
    _AGENTS[AgentRole.CRITIC.value] = critic

def _extract_actions(state_update: dict, agent_role: str) -> list:
    """Helper to simulate extracting action logs. In a real system, agents would push these to a DB."""
    # For now, we rely on the DB service called within the agent's log_action method.
    # The state update here just returns the changes to the StateGraph.
    return []

async def plan_node(state: ResearchState) -> Dict[str, Any]:
    logger.info("executing_node", node="plan")
    agent: PlannerAgent = _AGENTS[AgentRole.PLANNER.value]
    result = await agent.execute(dict(state))
    # Return state updates
    return {
        "plan": result.get("plan"),
        "status": result.get("status", "PLANNING_COMPLETED"),
        "current_agent": AgentRole.PLANNER.value,
        "errors": result.get("errors", [])
    }

async def research_node(state: ResearchState) -> Dict[str, Any]:
    logger.info("executing_node", node="research")
    agent: ResearchAgent = _AGENTS[AgentRole.RESEARCHER.value]
    result = await agent.execute(dict(state))
    return {
        "findings": result.get("findings", []),
        "status": result.get("status", "RESEARCH_COMPLETED"),
        "current_agent": AgentRole.RESEARCHER.value,
        "errors": result.get("errors", [])
    }

async def analyze_node(state: ResearchState) -> Dict[str, Any]:
    logger.info("executing_node", node="analyze")
    agent: AnalystAgent = _AGENTS[AgentRole.ANALYST.value]
    result = await agent.execute(dict(state))
    return {
        "analysis": result.get("analysis"),
        "status": result.get("status", "ANALYSIS_COMPLETED"),
        "current_agent": AgentRole.ANALYST.value,
        "errors": result.get("errors", [])
    }

async def write_node(state: ResearchState) -> Dict[str, Any]:
    logger.info("executing_node", node="write")
    agent: WriterAgent = _AGENTS[AgentRole.WRITER.value]
    result = await agent.execute(dict(state))
    
    # If we are visiting this node, it might be a revision.
    # We increment the revision count if it's not the first time.
    # The graph structure determines when it's a revision.
    
    return {
        "draft_report": result.get("draft_report"),
        "status": result.get("status", "WRITING_COMPLETED"),
        "current_agent": AgentRole.WRITER.value,
        "errors": result.get("errors", [])
    }

async def review_node(state: ResearchState) -> Dict[str, Any]:
    logger.info("executing_node", node="review")
    agent: CriticAgent = _AGENTS[AgentRole.CRITIC.value]
    result = await agent.execute(dict(state))
    return {
        "review": result.get("review"),
        "approved": result.get("approved", False),
        "status": result.get("status", "REVIEW_COMPLETED"),
        "current_agent": AgentRole.CRITIC.value,
        "errors": result.get("errors", []),
        "revision_count": 1 # This will be added via operator.add reducer
    }

async def human_review_node(state: ResearchState) -> Dict[str, Any]:
    """
    A dummy node that acts as a placeholder for human review.
    In a real system, the graph execution would pause here (using checkpointers)
    and resume when the human provides input via an API endpoint.
    """
    logger.info("executing_node", node="human_review")
    return {
        "status": "WAITING_FOR_HUMAN",
        "current_agent": "HUMAN"
    }

# --- Conditional Routing Functions ---

def should_revise(state: ResearchState) -> Literal["revise", "approve"]:
    """Determine if the report needs revision based on critic's review."""
    approved = state.get("approved", False)
    revisions = state.get("revision_count", 0)
    
    if not approved and revisions < 3:
        logger.info("routing", decision="revise", revisions=revisions)
        return "revise"
    
    logger.info("routing", decision="approve", revisions=revisions)
    return "approve"

def needs_human_approval(state: ResearchState) -> Literal["human_review", "complete"]:
    """Determine if human approval is required before completion."""
    if state.get("require_human_approval", False):
        logger.info("routing", decision="human_review")
        return "human_review"
    
    logger.info("routing", decision="complete")
    return "complete"

def handle_human_decision(state: ResearchState) -> Literal["complete", "revise"]:
    """Route based on human's decision (set via API)."""
    approved = state.get("human_approved", False)
    if approved:
        return "complete"
    return "revise"
