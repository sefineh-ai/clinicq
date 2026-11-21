from typing import Any
import json
import logging
from fastapi import WebSocket

logger = logging.getLogger("clinicq.events")


class ConnectionManager:
    def __init__(self):
        # Active connections: set of WebSocket objects
        self.active_connections: set[WebSocket] = set()
        # Doctor-specific connections: doctor_id -> set of WebSocket objects
        self.doctor_connections: dict[int, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, doctor_id: int | None = None):
        await websocket.accept()
        self.active_connections.add(websocket)
        if doctor_id is not None:
            if doctor_id not in self.doctor_connections:
                self.doctor_connections[doctor_id] = set()
            self.doctor_connections[doctor_id].add(websocket)
        logger.info(f"WebSocket connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, doctor_id: int | None = None):
        self.active_connections.discard(websocket)
        if doctor_id is not None and doctor_id in self.doctor_connections:
            self.doctor_connections[doctor_id].discard(websocket)
            if not self.doctor_connections[doctor_id]:
                del self.doctor_connections[doctor_id]
        logger.info(f"WebSocket disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]):
        """Broadcast an event to all connected clients (receptionists, waiting screens, doctors)."""
        payload = json.dumps(message, default=str)
        dead_connections = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning(f"Error sending message to websocket: {e}")
                dead_connections.append(connection)
        
        for dead in dead_connections:
            self.active_connections.discard(dead)

    async def broadcast_to_doctor(self, doctor_id: int, message: dict[str, Any]):
        """Broadcast an event specifically to clients subscribed to a doctor's queue."""
        payload = json.dumps(message, default=str)
        if doctor_id in self.doctor_connections:
            dead_connections = []
            for connection in list(self.doctor_connections[doctor_id]):
                try:
                    await connection.send_text(payload)
                except Exception as e:
                    logger.warning(f"Error sending to doctor {doctor_id} socket: {e}")
                    dead_connections.append(connection)
            for dead in dead_connections:
                self.doctor_connections[doctor_id].discard(dead)
        # Also always broadcast queue updates to the general pool for public displays
        await self.broadcast(message)


# Global singleton instance
ws_manager = ConnectionManager()
