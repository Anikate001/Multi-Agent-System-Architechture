import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any

from schemas.api import ResearchRequest, ResearchResponse, TaskStatusResponse, HealthResponse
from schemas.research import ResearchTask, ResearchReport
from orchestration.graph import ResearchOrchestrator
from services.db_service import DatabaseService
from services.cache_service import CacheService
from config.settings import get_settings
from api.websocket import manager

logger = structlog.get_logger(__name__)
router = APIRouter()

# Dependency injection placeholders
def get_db():
    settings = get_settings()
    return DatabaseService(settings.database_url)

def get_cache():
    settings = get_settings()
    return CacheService(settings.redis_url)

def get_orchestrator(db=Depends(get_db), cache=Depends(get_cache)):
    return ResearchOrchestrator(get_settings(), db, cache)

async def run_task_background(task_id: str, request: ResearchRequest, orchestrator: ResearchOrchestrator):
    """Background task to run the research orchestrator."""
    task = ResearchTask(
        query=request.query,
        depth=request.depth,
        max_sources=request.max_sources,
        require_human_approval=request.require_approval,
        include_code_analysis=False
    )
    
    async def callback(update_data: dict):
        # Broadcast to WebSocket
        await manager.broadcast_to_task(task_id, {
            "type": "status",
            "data": update_data
        })
        
    try:
        report = await orchestrator.run(task, task_id, callback=callback)
        await manager.broadcast_to_task(task_id, {
            "type": "report",
            "data": report.model_dump()
        })
    except Exception as e:
        logger.exception("task_execution_failed", task_id=task_id, error=str(e))
        await manager.broadcast_to_task(task_id, {
            "type": "error",
            "data": {"message": str(e)}
        })

@router.post("/research", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest, 
    background_tasks: BackgroundTasks,
    orchestrator: ResearchOrchestrator = Depends(get_orchestrator),
    db: DatabaseService = Depends(get_db)
):
    """Start a new research task."""
    task_id = str(uuid.uuid4())
    logger.info("starting_research_task", task_id=task_id, query=request.query)
    
    await db.save_task(task_id, request.query, "STARTING")
    
    background_tasks.add_task(run_task_background, task_id, request, orchestrator)
    
    return ResearchResponse(
        task_id=task_id,
        status="STARTING",
        message="Research task initiated"
    )

@router.get("/research/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    orchestrator: ResearchOrchestrator = Depends(get_orchestrator)
):
    """Get the current status of a research task."""
    state = await orchestrator.get_state(task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return TaskStatusResponse(
        task_id=task_id,
        status=state.get("status", "UNKNOWN"),
        current_agent=state.get("current_agent", ""),
        progress_pct=0.0, # Calculate based on status if needed
        agent_actions=state.get("agent_actions", []),
        token_usage=state.get("token_usage", {}),
        estimated_cost=0.0,
        report=state.get("draft_report")
    )

@router.post("/research/{task_id}/approve")
async def approve_task(
    task_id: str,
    orchestrator: ResearchOrchestrator = Depends(get_orchestrator)
):
    """Approve a task waiting for human review."""
    await orchestrator.approve_task(task_id)
    return {"status": "APPROVED", "message": "Task approved and resumed"}

@router.post("/research/{task_id}/reject")
async def reject_task(
    task_id: str,
    feedback: Dict[str, str],
    orchestrator: ResearchOrchestrator = Depends(get_orchestrator)
):
    """Reject a task with feedback, triggering a revision loop."""
    if "feedback" not in feedback:
        raise HTTPException(status_code=400, detail="Feedback is required")
        
    await orchestrator.reject_task(task_id, feedback["feedback"])
    return {"status": "REJECTED", "message": "Task rejected, revision requested"}

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="OK",
        version="1.0.0",
        uptime_seconds=0,
        db_connected=True,
        redis_connected=True,
        active_tasks=0
    )
