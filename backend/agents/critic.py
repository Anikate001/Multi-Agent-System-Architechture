from typing import Dict, Any, List
import structlog
from pydantic import BaseModel, Field

from agents.base import BaseAgent
from schemas.agents import AgentRole
from schemas.research import ResearchReport
from prompts.templates import PromptTemplates

logger = structlog.get_logger(__name__)

APPROVAL_SCORE = 7

class ReviewFeedback(BaseModel):
    quality_score: int = Field(..., description="Score from 1 to 10")
    hallucinations_detected: List[str] = Field(default_factory=list, description="Claims made without source support")
    citation_issues: List[str] = Field(default_factory=list, description="Issues with how sources are cited")
    coherence_issues: List[str] = Field(default_factory=list, description="Issues with narrative flow or logic")
    specific_revisions_requested: str = Field(..., description="Actionable feedback for the Writer")
    approved: bool = Field(..., description="True if score >= 7 and no major issues")

class CriticAgent(BaseAgent):
    """Reviews draft reports for accuracy, citations, and coherence."""
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        draft_dict = state.get("draft_report")
        
        logger.info("critic_started", has_draft=bool(draft_dict))
        
        if not draft_dict:
            return {"errors": ["No draft report to review"], "status": "REVIEW_FAILED"}
            
        system_prompt = PromptTemplates.critic_prompt()
        
        # Give the Critic the evidence the Writer had, so it can check claims against sources.
        source_lines, seen = [], set()
        for finding in state.get("findings", []):
            for src in finding.get("sources", []):
                url = src.get("url", "")
                if url and url not in seen:
                    seen.add(url)
                    source_lines.append(f"[{len(seen)}] {src.get('title', '')} ({url})\n{src.get('snippet', '')}")
        sources_text = "\n\n".join(source_lines) or "(no sources were retrieved)"

        user_message = (
            "Review the draft research report below. Flag any claim the SOURCES do not support, "
            "check that citations point to real sources from the list, and judge overall quality.\n\n"
            f"SOURCES:\n{sources_text}\n\nDRAFT REPORT:\n{str(draft_dict)}"
        )
        
        async def review_draft():
            return await self.llm.generate_structured(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                output_schema=ReviewFeedback
            )
            
        review_result, latency, success = await self._safe_execute(review_draft)
        
        if success:
            review: ReviewFeedback = review_result
            # Approval is decided in code, not left to the model: score >= 7 and no unsupported claims.
            review.approved = review.quality_score >= APPROVAL_SCORE and not review.hallucinations_detected
            
            await self.log_action(
                action="review_report",
                input_data={"draft_sections": len(draft_dict.get("sections", []))},
                output_data={"score": review.quality_score, "approved": review.approved},
                tokens=self.llm.total_tokens_used,
                latency_ms=latency,
                success=True
            )
            
            return {
                "review": review.model_dump(), 
                "approved": review.approved,
                "status": "REVIEW_COMPLETED",
                "current_agent": self.role.value
            }
        else:
            await self.log_action(
                action="review_report",
                input_data={},
                output_data={"error": str(review_result)},
                tokens=0,
                latency_ms=latency,
                success=False
            )
            return {"errors": [str(review_result)], "status": "REVIEW_FAILED", "current_agent": self.role.value}
