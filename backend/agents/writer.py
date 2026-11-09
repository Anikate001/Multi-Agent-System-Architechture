from typing import Dict, Any, List
import structlog
import datetime

from agents.base import BaseAgent
from schemas.agents import AgentRole
from schemas.research import ResearchReport, ReportSection, Citation, Source
from prompts.templates import PromptTemplates

logger = structlog.get_logger(__name__)

class WriterAgent(BaseAgent):
    """Writes the final structured report based on analysis and findings."""
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        analysis = state.get("analysis", {})
        findings = state.get("findings", [])
        # The Critic (and a human rejection) put actionable notes in `specific_revisions_requested`.
        review = state.get("review") or {}
        previous_feedback = review.get("specific_revisions_requested", "")
        issues = review.get("hallucinations_detected", []) + review.get("citation_issues", []) + review.get("coherence_issues", [])
        if issues:
            previous_feedback += "\nIssues found:\n" + "\n".join(f"- {i}" for i in issues)
        
        logger.info("writer_started", has_feedback=bool(previous_feedback))
        
        system_prompt = PromptTemplates.writer_prompt()
        
        # Compile context
        context = f"Original Query: {query}\n\n"
        if previous_feedback:
            context += f"CRITICAL REVISION FEEDBACK:\n{previous_feedback}\n\n"
            
        context += f"Analysis Narrative:\n{analysis.get('core_narrative', '')}\n\n"
        
        context += "Source Materials:\n"
        source_map = {} # URL to Source mapping
        for i, f in enumerate(findings):
            for src in f.get('sources', []):
                url = src.get('url', '')
                if url and url not in source_map:
                    source_map[url] = src
                    context += f"[{len(source_map)}] {src.get('title', 'Unknown')} ({url})\nSnippets: {src.get('snippet', '')}\n\n"
        
        user_message = f"Write a comprehensive, publication-quality research report based on the provided analysis and source materials. YOU MUST CITE YOUR SOURCES inline using [Source URL].\n\n{context}"
        
        async def write_report():
            report_schema = await self.llm.generate_structured(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                output_schema=ResearchReport
            )
            # Ensure metadata and timestamps are set
            report_schema.generated_at = datetime.datetime.now(datetime.timezone.utc)
            
            # Map URLs to full Source objects in bibliography
            bib_sources = []
            for url, src_data in source_map.items():
                bib_sources.append(Source(**src_data))
            report_schema.bibliography = bib_sources
            report_schema.total_citations = sum(len(sec.citations) for sec in report_schema.sections)
            return report_schema
            
        report_result, latency, success = await self._safe_execute(write_report)
        
        if success:
            await self.log_action(
                action="write_report",
                input_data={"revision": state.get("revision_count", 0)},
                output_data={"sections": len(report_result.sections)},
                tokens=self.llm.total_tokens_used,
                latency_ms=latency,
                success=True
            )
            return {"draft_report": report_result.model_dump(mode="json"), "status": "WRITING_COMPLETED", "current_agent": self.role.value}
        else:
            await self.log_action(
                action="write_report",
                input_data={},
                output_data={"error": str(report_result)},
                tokens=0,
                latency_ms=latency,
                success=False
            )
            return {"errors": [str(report_result)], "status": "WRITING_FAILED", "current_agent": self.role.value}
