from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import structlog
import sys
import time

from api.routes import router as api_router
from api.websocket import manager
from config.settings import get_settings
from services.db_service import DatabaseService
from services.cache_service import CacheService
from orchestration.graph import ResearchOrchestrator
from schemas.api import HealthResponse

# Setup structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger(__name__)

app = FastAPI(
    title="Nexus Research Platform",
    description="Multi-Agent AI Research Orchestration API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")  # path used by the Streamlit frontend

_STARTED_AT = time.time()


@app.on_event("startup")
async def startup_event():
    """Create ONE database, cache and orchestrator for the whole app.

    LangGraph keeps run state in the orchestrator's checkpointer, so every request
    (status, approve, reject) must talk to the same orchestrator instance.
    """
    logger.info("nexus_api_starting")
    settings = get_settings()
    db = DatabaseService(settings.database_url)
    await db.init_db()
    cache = CacheService(settings.redis_url)
    await cache.connect()
    app.state.settings = settings
    app.state.db = db
    app.state.cache = cache
    app.state.orchestrator = ResearchOrchestrator(settings, db, cache)
    app.state.tasks = {}


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("nexus_api_shutting_down")
    await app.state.cache.disconnect()
    await app.state.db.dispose()


@app.get("/health", response_model=HealthResponse)
@app.get("/api/health", response_model=HealthResponse, include_in_schema=False)
async def health_check():
    db_ok = await app.state.db.health_check()
    redis_ok = await app.state.cache.health_check()
    running = sum(1 for t in app.state.tasks.values() if not t.get("finished_at"))
    return HealthResponse(
        status="healthy" if db_ok and redis_ok else "degraded",
        version="1.0.0",
        uptime_seconds=round(time.time() - _STARTED_AT, 1),
        db_connected=db_ok,
        redis_connected=redis_ok,
        active_tasks=running,
    )


async def _ws_handler(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        while True:
            # Clients don't send messages; keep the connection open for server pushes.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)


@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await _ws_handler(websocket, task_id)


@app.websocket("/ws/research/{task_id}")
async def websocket_research_endpoint(websocket: WebSocket, task_id: str):
    """Alias for the path the Streamlit frontend uses."""
    await _ws_handler(websocket, task_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
