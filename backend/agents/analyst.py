from typing import Dict, Any, List
import structlog
from pydantic import BaseModel, Field

from agents.base import BaseAgent
from schemas.agents import AgentRole
from prompts.templates import PromptTemplates

logger = structlog.get_logger(__name__)

class SynthesizedAnalysis(BaseModel):
    core_narrative: str = Field(..., description="The main synthesized narrative from all findings")
    identified_patterns: List[str] = Field(..., description="Common themes or patterns across sources")
    contradictions: List[str] = Field(default_factory=list, description="Conflicting information found in sources")
    knowledge_gaps: List[str] = Field(default_factory=list, description="Missing information that couldn't be found")
    overall_confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")

class AnalystAgent(BaseAgent):
    """Synthesizes raw findings into coherent insights, identifying patterns and contradictions."""
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        findings = state.get("findings", [])
        
        logger.info("analyst_started", findings_count=len(findings))
        
        if not findings:
            return {"errors": ["No findings to analyze"], "status": "ANALYSIS_FAILED"}
            
        system_prompt = PromptTemplates.analyst_prompt()
        
        # Prepare context from findings
        findings_text = ""
        for i, f in enumerate(findings):
            topic = f.get('topic', 'Unknown')
            summary = f.get('summary', '')
            points = "\n".join([f"- {p}" for p in f.get('key_points', [])])
            findings_text += f"\nFinding {i+1} ({topic}):\n{summary}\nKey Points:\n{points}\n"
            
        user_message = f"Original Query: {query}\n\nSynthesize the following research findings. Identify patterns, contradictions, and gaps.\n\n{findings_text}"
        
        async def analyze_data():
            return await self.llm.generate_structured(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                output_schema=SynthesizedAnalysis
            )
            
        analysis_result, latency, success = await self._safe_execute(analyze_data)
        
        if success:
            analysis = analysis_result
            await self.log_action(
                action="analyze_findings",
                input_data={"findings_count": len(findings)},
                output_data={"patterns": len(analysis.identified_patterns), "confidence": analysis.overall_confidence},
                tokens=self.llm.total_tokens_used,
                latency_ms=latency,
                success=True
            )
            return {"analysis": analysis.model_dump(), "status": "ANALYSIS_COMPLETED", "current_agent": self.role.value}
        else:
            await self.log_action(
                action="analyze_findings",
                input_data={},
                output_data={"error": str(analysis_result)},
                tokens=0,
                latency_ms=latency,
                success=False
            )
            return {"errors": [str(analysis_result)], "status": "ANALYSIS_FAILED", "current_agent": self.role.value}
