from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import structlog
import json

logger = structlog.get_logger(__name__)

class ConnectionManager:
    def __init__(self):
        # task_id -> list of active websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
        logger.info("websocket_connected", task_id=task_id)

    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            if websocket in self.active_connections[task_id]:
                self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info("websocket_disconnected", task_id=task_id)

    async def broadcast_to_task(self, task_id: str, message: dict):
        """Send a message to all connected clients for a specific task."""
        if task_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning("websocket_send_error", task_id=task_id, error=str(e))
                    dead_connections.append(connection)
            
            # Cleanup dead connections
            for dead_conn in dead_connections:
                self.disconnect(dead_conn, task_id)

manager = ConnectionManager()
