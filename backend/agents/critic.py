from typing import Dict, Any, List
import structlog
from pydantic import BaseModel, Field

from agents.base import BaseAgent
from schemas.agents import AgentRole
from schemas.research import ResearchReport
from prompts.templates import PromptTemplates

logger = structlog.get_logger(__name__)

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
        
        # In a real system, we'd also pass in the raw sources to allow the critic to cross-reference
        # For simplicity in this implementation, we just pass the draft which includes citations
        user_message = f"Please review the following draft research report. Check for unsupported claims, citation formatting, and overall quality.\n\nDraft Report:\n{str(draft_dict)}"
        
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
