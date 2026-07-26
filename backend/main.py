from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import structlog
import sys

from api.routes import router as api_router
from api.websocket import manager
from config.settings import get_settings
from services.db_service import DatabaseService
from services.cache_service import CacheService

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

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        while True:
            # We don't really expect client messages, just keep connection open
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)

@app.on_event("startup")
async def startup_event():
    logger.info("nexus_api_starting")
    settings = get_settings()
    db = DatabaseService(settings.database_url)
    await db.init_db()
    await db.dispose()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("nexus_api_shutting_down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
