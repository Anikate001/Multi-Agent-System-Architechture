from typing import Dict, Any, List
import structlog
from pydantic import BaseModel, Field

from agents.base import BaseAgent
from schemas.agents import AgentRole
from prompts.templates import PromptTemplates

logger = structlog.get_logger(__name__)

class TaskPlan(BaseModel):
    id: str = Field(..., description="Unique task identifier")
    description: str = Field(..., description="Detailed description of the task")
    dependencies: List[str] = Field(default_factory=list, description="IDs of tasks that must be completed first")
    estimated_complexity: str = Field(..., description="Low, Medium, or High")
    required_tools: List[str] = Field(default_factory=list, description="Tools needed for this task")

class ExecutionPlan(BaseModel):
    query: str = Field(..., description="The original normalized query")
    sub_tasks: List[TaskPlan] = Field(..., description="Ordered list of sub-tasks")
    overall_strategy: str = Field(..., description="The high-level approach to solving the query")

class PlannerAgent(BaseAgent):
    """Decomposes complex research queries into structured sub-tasks."""
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        depth = state.get("depth", "standard")
        
        logger.info("planner_started", query=query, depth=depth)
        
        system_prompt = PromptTemplates.planner_prompt()
        user_message = f"Please create a research plan for the following query. Depth level: {depth}.\n\nQuery: {query}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        async def generate_plan():
            return await self.llm.generate_structured(messages, ExecutionPlan)
            
        plan_result, latency, success = await self._safe_execute(generate_plan)
        
        if success:
            plan = plan_result
            await self.log_action(
                action="create_plan",
                input_data={"query": query, "depth": depth},
                output_data=plan.model_dump(),
                tokens=self.llm.total_tokens_used, # Approximation, would be tracked per call ideally
                latency_ms=latency,
                success=True
            )
            return {"plan": plan.model_dump(), "status": "PLANNING_COMPLETED", "current_agent": self.role.value}
        else:
            await self.log_action(
                action="create_plan",
                input_data={"query": query},
                output_data={"error": str(plan_result)},
                tokens=0,
                latency_ms=latency,
                success=False
            )
            # Fallback plan for graceful degradation
            fallback_plan = ExecutionPlan(
                query=query,
                overall_strategy="Direct web search due to planning failure.",
                sub_tasks=[TaskPlan(id="t1", description=query, estimated_complexity="Medium")]
            )
            return {"plan": fallback_plan.model_dump(), "errors": [str(plan_result)], "status": "PLANNING_FAILED", "current_agent": self.role.value}
