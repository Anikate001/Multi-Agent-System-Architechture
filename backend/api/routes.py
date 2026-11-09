import time
import uuid
from datetime import datetime, timezone
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
_NODE_AGENT = {"plan": "planner", "research": "researcher", "analyze": "analyst", "write": "writer", "review": "critic"}


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

    llm = getattr(app.state.orchestrator, "llm", None)
    clock = {"t": time.time(), "tokens": getattr(llm, "total_tokens_used", 0)}
    registry[task_id]["actions"] = []

    async def callback(update_data: dict):
        node = update_data.get("node")
        registry[task_id]["last_node"] = node
        # Record time and tokens per agent step for the dashboard (one run at a time on the demo,
        # so the token delta belongs to this task)
        now, tokens = time.time(), getattr(llm, "total_tokens_used", 0)
        if node in _NODE_PROGRESS:
            registry[task_id]["actions"].append({
                "agent": _NODE_AGENT[node],
                "action": node,
                "latency_ms": round((now - clock["t"]) * 1000),
                "tokens_used": max(tokens - clock["tokens"], 0),
                "timestamp": datetime.fromtimestamp(now, timezone.utc),
            })
        clock.update(t=now, tokens=tokens)
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


# Rough blended Flash-tier price per token, for the dashboard's cost estimate
_USD_PER_TOKEN = 0.25 / 1_000_000


def _agents_summary(actions: list, current_agent: str, status: str) -> dict:
    """Per-agent totals in the shape the Streamlit tracker and analytics panels read."""
    agents = {}
    for role in _NODE_AGENT.values():
        mine = [a for a in actions if a["agent"] == role]
        if mine:
            state = "completed"
        elif role == current_agent and status == "running":
            state = "active"
        else:
            state = "pending"
        tokens = sum(a["tokens_used"] for a in mine)
        agents[role] = {
            "status": state,
            "tokens": tokens,
            "latency_ms": sum(a["latency_ms"] for a in mine),
            "cost_usd": round(tokens * _USD_PER_TOKEN, 6),
            "runs": len(mine),
        }
    return agents


def _report_for_frontend(report: dict, values: dict) -> dict:
    """The stored report plus the fields the Streamlit report viewer and citation panel read."""
    review = values.get("review") or {}
    body = _report_markdown({**report, "title": ""}).lstrip("# \n")
    citations = [
        {
            "id": i,
            "text": c.get("claim", ""),
            "url": c.get("source_url", ""),
            "source_title": c.get("source_title", ""),
            "verified": c.get("verified", False),
            "confidence": c.get("confidence", 0.0),
        }
        for i, c in enumerate((c for s in report.get("sections", []) for c in s.get("citations", [])), 1)
    ]
    sources = [{**s, "relevance": s.get("relevance_score", 0)} for s in report.get("bibliography", [])]
    return {
        **report,
        "markdown": body,
        "quality_score": review.get("quality_score", 0),
        "citations": citations,
        "sources": sources,
        "metadata": {
            **(report.get("metadata") or {}),
            "word_count": len(body.split()),
            "sections": len(report.get("sections", [])),
            "revisions": max(int(values.get("revision_count", 0)) - 1, 0),
        },
    }


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
def _check_run_limits(request: Request) -> None:
    """Reject a new run when the demo's daily or concurrent run limit is reached."""
    settings = request.app.state.settings
    registry = _tasks(request)
    if settings.max_concurrent_runs:
        running = sum(1 for t in registry.values() if not t.get("finished_at"))
        if running >= settings.max_concurrent_runs:
            raise HTTPException(status_code=429, detail="Another research run is in progress. Try again in a minute.")
    if settings.max_runs_per_day:
        today = datetime.now(timezone.utc).date()
        started_today = sum(
            1 for t in registry.values()
            if datetime.fromtimestamp(t["started_at"], timezone.utc).date() == today
        )
        if started_today >= settings.max_runs_per_day:
            raise HTTPException(
                status_code=429,
                detail=f"This demo's limit of {settings.max_runs_per_day} research runs per day has been reached. "
                "It resets at 00:00 UTC.",
            )


@router.post("/research", response_model=ResearchResponse)
async def start_research(body: ResearchRequest, background_tasks: BackgroundTasks, request: Request):
    """Start a new research task."""
    _check_run_limits(request)
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
    actions = _tasks(request).get(task_id, {}).get("actions") or []
    review = values.get("review") or {}
    return TaskStatusResponse(
        task_id=task_id,
        status=status,
        current_agent=values.get("current_agent", ""),
        progress_pct=progress,
        agent_actions=actions,
        agents=_agents_summary(actions, values.get("current_agent", ""), status),
        revision_count=max(int(values.get("revision_count", 0)) - 1, 0),
        quality_scores=[review["quality_score"]] if review.get("quality_score") else [],
        token_usage=values.get("token_usage", {}),
        estimated_cost=round(sum(a["tokens_used"] for a in actions) * _USD_PER_TOKEN, 6),
        report=values.get("draft_report") if status == "completed" else None,
    )


@router.get("/research/{task_id}/report")
async def get_report(task_id: str, request: Request):
    """Return the latest report draft (final once status is 'completed')."""
    _, values = await _load(request, task_id)
    report = values.get("draft_report")
    if not report:
        raise HTTPException(status_code=404, detail="Report not ready yet")
    return _report_for_frontend(report, values)


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
