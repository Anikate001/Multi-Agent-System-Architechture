import pytest
from backend.schemas.research import ResearchTask, Source, Citation, ResearchFinding, ReportSection, ResearchReport

def test_research_task_creation():
    task = ResearchTask(
        query="Quantum computing advances",
        depth="standard",
        max_sources=10,
        require_human_approval=True
    )
    assert task.query == "Quantum computing advances"
    assert task.require_human_approval is True

def test_source_model():
    source = Source(
        url="https://example.com",
        title="Example",
        snippet="An example snippet",
        relevance_score=0.9
    )
    assert source.url == "https://example.com"
    
def test_report_serialization():
    report = ResearchReport(
        title="Test Report",
        abstract="Test Abstract",
        sections=[],
        bibliography=[],
        metadata={},
        generated_at="2026-05-22",
        total_citations=0,
        quality_score=9.5
    )
    dump = report.model_dump()
    assert dump["title"] == "Test Report"
