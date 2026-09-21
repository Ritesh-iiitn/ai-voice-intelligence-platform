"""FastAPI WebSocket connection manager and event routing for real-time call telemetry."""

from __future__ import annotations

import collections
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from q4_realtime.schemas import WebSocketMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections partitioned by call_id and global supervisor broadcasts."""

    def __init__(self):
        # Maps call_id -> list of connected WebSockets
        self.active_call_connections: Dict[str, List[WebSocket]] = collections.defaultdict(list)
        # Global dashboard listeners (e.g. multi-call supervisor panel)
        self.global_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, call_id: Optional[str] = None) -> None:
        """Accept new WebSocket connection and assign to call channel or global pool."""
        await websocket.accept()
        if call_id and call_id != "global":
            self.active_call_connections[call_id].append(websocket)
            logger.info("Client connected to call channel: %s", call_id)
        else:
            self.global_connections.append(websocket)
            logger.info("Client connected to global supervisor stream")

    def disconnect(self, websocket: WebSocket, call_id: Optional[str] = None) -> None:
        """Remove WebSocket connection safely upon disconnect."""
        if call_id and call_id in self.active_call_connections:
            if websocket in self.active_call_connections[call_id]:
                self.active_call_connections[call_id].remove(websocket)
            if not self.active_call_connections[call_id]:
                self.active_call_connections.pop(call_id, None)
            logger.info("Client disconnected from call channel: %s", call_id)

        if websocket in self.global_connections:
            self.global_connections.remove(websocket)
            logger.info("Client disconnected from global stream")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """Send a direct JSON message to a single WebSocket client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning("Failed to send direct message to websocket: %s", e)

    async def broadcast_to_call(self, call_id: str, message: WebSocketMessage | Dict[str, Any]) -> None:
        """Broadcast an event to all subscribers listening to this specific call_id and global listeners."""
        payload = message.model_dump() if isinstance(message, WebSocketMessage) else message
        payload_str = json.dumps(payload)

        # 1. Send to call subscribers
        subscribers = list(self.active_call_connections.get(call_id, []))
        dead_connections = []
        for ws in subscribers:
            try:
                await ws.send_text(payload_str)
            except Exception:
                dead_connections.append(ws)

        for dead in dead_connections:
            self.disconnect(dead, call_id)

        # 2. Also send to global supervisor listeners
        global_dead = []
        for ws in list(self.global_connections):
            try:
                await ws.send_text(payload_str)
            except Exception:
                global_dead.append(ws)

        for dead in global_dead:
            self.disconnect(dead, None)

    async def broadcast_global(self, message: WebSocketMessage | Dict[str, Any]) -> None:
        """Broadcast an event to all active connections across all channels."""
        payload = message.model_dump() if isinstance(message, WebSocketMessage) else message
        payload_str = json.dumps(payload)

        all_connections = set(self.global_connections)
        for pool in self.active_call_connections.values():
            all_connections.update(pool)

        for ws in list(all_connections):
            try:
                await ws.send_text(payload_str)
            except Exception:
                pass


# Global singleton manager
_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Retrieve or initialize the global ConnectionManager singleton."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
