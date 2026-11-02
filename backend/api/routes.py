import time
import uuid
from typing import Any, Dict

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import PlainTextResponse

from schemas.api import ResearchRequest, ResearchResponse, TaskStatusResponse
from schemas.research import ResearchTask
from api.websocket import manager

logger = structlog.get_logger(__name__)
router = APIRouter()

# Order of the workflow nodes, used to estimate progress.
_NODE_PROGRESS = {"plan": 15.0, "research": 40.0, "analyze": 60.0, "write": 80.0, "review": 95.0}


# --------------------------------------------------------------------------- shared services
# The orchestrator, database and cache are created once at startup (see main.py) and shared
# by every request. A per-request orchestrator would start with an empty LangGraph
# checkpointer, so status, approve and reject could never find the task.
def _orchestrator(request: Request):
    return request.app.state.orchestrator


def _db(request: Request):
    return request.app.state.db


def _tasks(request: Request) -> Dict[str, Dict[str, Any]]:
    """In-process registry: task_id -> {query, started_at, failed, error, last_node}."""
    return request.app.state.tasks


# --------------------------------------------------------------------------- background runner
async def run_task_background(task_id: str, request_body: ResearchRequest, app) -> None:
    """Run the research workflow and stream progress over WebSockets."""
    registry = app.state.tasks
    task = ResearchTask(
        query=request_body.query,
        depth=request_body.depth,
        max_sources=request_body.max_sources,
        require_human_approval=request_body.require_approval,
        include_code_analysis=False,
    )

    async def callback(update_data: dict):
        registry[task_id]["last_node"] = update_data.get("node")
        await manager.broadcast_to_task(task_id, {"type": "status", "data": update_data})

    try:
        report = await app.state.orchestrator.run(task, task_id, callback=callback)
        registry[task_id]["finished_at"] = time.time()
        await manager.broadcast_to_task(task_id, {"type": "report", "data": report.model_dump(mode="json")})
    except Exception as e:
        logger.exception("task_execution_failed", task_id=task_id, error=str(e))
        registry[task_id].update(failed=True, error=str(e), finished_at=time.time())
        await manager.broadcast_to_task(task_id, {"type": "error", "data": {"message": str(e)}})


# --------------------------------------------------------------------------- status helpers
def _public_status(task_id: str, snapshot, values: dict, registry: dict) -> str:
    """Map internal LangGraph state to the statuses the frontend understands:
    running | needs_approval | completed | failed."""
    info = registry.get(task_id, {})
    if info.get("failed"):
        return "failed"
    if snapshot is not None and snapshot.next and "human_review" in snapshot.next:
        return "needs_approval"
    if snapshot is not None and not snapshot.next and values.get("draft_report"):
        return "completed"
    return "running"


def _snapshot(orchestrator, task_id: str):
    try:
        return orchestrator.graph.get_state({"configurable": {"thread_id": task_id}})
    except Exception:
        return None


async def _load(request: Request, task_id: str):
    orchestrator = _orchestrator(request)
    snapshot = _snapshot(orchestrator, task_id)
    values = (snapshot.values if snapshot is not None else None) or {}
    if not values:
        values = await orchestrator.get_state(task_id) or {}
    if not values and task_id not in _tasks(request):
        raise HTTPException(status_code=404, detail="Task not found")
    return snapshot, values


def _report_markdown(report: dict) -> str:
    lines = [f"# {report.get('title', 'Research report')}", "", report.get("abstract", ""), ""]
    for section in report.get("sections", []):
        lines += [f"## {section.get('title', '')}", "", section.get("content", ""), ""]
    bib = report.get("bibliography", [])
    if bib:
        lines += ["## Sources", ""]
        lines += [f"{i}. [{s.get('title') or s.get('url')}]({s.get('url')})" for i, s in enumerate(bib, 1)]
    return "\n".join(lines).strip() + "\n"


# --------------------------------------------------------------------------- endpoints
@router.post("/research", response_model=ResearchResponse)
async def start_research(body: ResearchRequest, background_tasks: BackgroundTasks, request: Request):
    """Start a new research task."""
    task_id = str(uuid.uuid4())
    logger.info("starting_research_task", task_id=task_id, query=body.query)
    _tasks(request)[task_id] = {"query": body.query, "started_at": time.time(), "failed": False}
    await _db(request).save_task(task_id, body.query, "STARTING")
    background_tasks.add_task(run_task_background, task_id, body, request.app)
    return ResearchResponse(task_id=task_id, status="STARTING", message="Research task initiated")


@router.get("/research/{task_id}", response_model=TaskStatusResponse)
@router.get("/research/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, request: Request):
    """Get the current status of a research task."""
    snapshot, values = await _load(request, task_id)
    status = _public_status(task_id, snapshot, values, _tasks(request))
    last_node = _tasks(request).get(task_id, {}).get("last_node")
    progress = 100.0 if status == "completed" else _NODE_PROGRESS.get(last_node, 5.0)
    return TaskStatusResponse(
        task_id=task_id,
        status=status,
        current_agent=values.get("current_agent", ""),
        progress_pct=progress,
        agent_actions=values.get("agent_actions", []),
        token_usage=values.get("token_usage", {}),
        estimated_cost=0.0,
        report=values.get("draft_report") if status == "completed" else None,
    )


@router.get("/research/{task_id}/report")
async def get_report(task_id: str, request: Request):
    """Return the latest report draft (final once status is 'completed')."""
    _, values = await _load(request, task_id)
    report = values.get("draft_report")
    if not report:
        raise HTTPException(status_code=404, detail="Report not ready yet")
    return report


@router.get("/research/{task_id}/export/markdown", response_class=PlainTextResponse)
async def export_markdown(task_id: str, request: Request):
    """Return the report as Markdown."""
    _, values = await _load(request, task_id)
    report = values.get("draft_report")
    if not report:
        raise HTTPException(status_code=404, detail="Report not ready yet")
    return _report_markdown(report)


@router.post("/research/{task_id}/approve")
async def approve_task(task_id: str, request: Request):
    """Approve a task waiting for human review."""
    snapshot, values = await _load(request, task_id)
    if _public_status(task_id, snapshot, values, _tasks(request)) != "needs_approval":
        raise HTTPException(status_code=409, detail="Task is not waiting for approval")
    await _orchestrator(request).approve_task(task_id)
    return {"status": "APPROVED", "message": "Task approved and completed"}


@router.post("/research/{task_id}/reject")
async def reject_task(task_id: str, feedback: Dict[str, str], request: Request, background_tasks: BackgroundTasks):
    """Reject a task with feedback, triggering a revision loop."""
    if "feedback" not in feedback:
        raise HTTPException(status_code=400, detail="Feedback is required")
    snapshot, values = await _load(request, task_id)
    if _public_status(task_id, snapshot, values, _tasks(request)) != "needs_approval":
        raise HTTPException(status_code=409, detail="Task is not waiting for approval")
    # The revision runs Writer and Critic again, so do it in the background.
    background_tasks.add_task(_orchestrator(request).reject_task, task_id, feedback["feedback"])
    return {"status": "REJECTED", "message": "Task rejected, revision requested"}


@router.get("/metrics")
async def metrics(request: Request):
    """Basic platform metrics for the dashboard."""
    registry = _tasks(request)
    orchestrator = _orchestrator(request)
    tokens, durations = 0, []
    for task_id, info in registry.items():
        snap = _snapshot(orchestrator, task_id)
        if snap is not None and snap.values:
            tokens += sum((snap.values.get("token_usage") or {}).values())
        if info.get("finished_at"):
            durations.append((info["finished_at"] - info["started_at"]) * 1000)
    return {
        "total_tasks": len(registry),
        "failed_tasks": sum(1 for i in registry.values() if i.get("failed")),
        "tokens_used": tokens,
        "avg_latency_ms": round(sum(durations) / len(durations)) if durations else 0,
        "agents": {},
    }
