from typing import Dict, Any, List
import structlog
import asyncio
from pydantic import BaseModel

from agents.base import BaseAgent
from schemas.agents import AgentRole
from schemas.research import ResearchFinding, Source
from prompts.templates import PromptTemplates

logger = structlog.get_logger(__name__)

class ExtractedInformation(BaseModel):
    topic: str
    summary: str
    key_points: List[str]
    confidence_score: float

class ResearchAgent(BaseAgent):
    """Executes research plan by gathering information from tools and summarizing."""
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        plan_dict = state.get("plan", {})
        query = state.get("query", "")
        max_sources = state.get("max_sources", 10)
        
        logger.info("researcher_started", task_count=len(plan_dict.get("sub_tasks", [])))
        
        sub_tasks = plan_dict.get("sub_tasks", [])
        if not sub_tasks:
            sub_tasks = [{"description": query}]
            
        all_findings = state.get("findings", [])
        search_tool = self.tools.get("web_search")
        
        if not search_tool:
            return {"errors": ["WebSearchTool not provided"], "status": "RESEARCH_FAILED"}

        async def research_task(task):
            task_desc = task.get("description", str(task))
            # 1. Search
            sources = await search_tool.search(task_desc, max_results=3)
            if not sources:
                return None
                
            # 2. Extract information using LLM
            system_prompt = PromptTemplates.researcher_prompt()
            context = "\n\n".join([f"Source: {s.url}\nTitle: {s.title}\nContent: {s.snippet}" for s in sources])
            user_message = f"Task: {task_desc}\n\nAnalyze the following search results and extract key information:\n{context}"
            
            try:
                extracted = await self.llm.generate_structured(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    output_schema=ExtractedInformation
                )
                
                finding = ResearchFinding(
                    topic=extracted.topic,
                    summary=extracted.summary,
                    key_points=extracted.key_points,
                    sources=sources,
                    confidence_score=extracted.confidence_score
                )
                return finding
            except Exception as e:
                logger.error("extraction_failed", task=task_desc, error=str(e))
                return None

        # Execute research concurrently for all sub-tasks
        results = await asyncio.gather(*[research_task(task) for task in sub_tasks], return_exceptions=True)
        
        new_findings = []
        for res in results:
            if isinstance(res, ResearchFinding):
                new_findings.append(res.model_dump(mode="json"))
            elif isinstance(res, Exception):
                logger.error("research_task_exception", error=str(res))
                
        all_findings.extend(new_findings)
        
        # Deduplicate findings if necessary (simplistic approach here)
        
        await self.log_action(
            action="conduct_research",
            input_data={"tasks": len(sub_tasks)},
            output_data={"findings_count": len(new_findings)},
            tokens=self.llm.total_tokens_used,
            latency_ms=0, # Tracked at higher level if needed
            success=True
        )
        
        return {"findings": all_findings, "status": "RESEARCH_COMPLETED", "current_agent": self.role.value}
