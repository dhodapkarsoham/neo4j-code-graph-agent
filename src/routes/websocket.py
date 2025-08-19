"""WebSocket routes for real-time communication."""

import json
import logging
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from src.agent import agent

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                # Remove failed connection
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

# Global WebSocket manager
websocket_manager = WebSocketManager()

async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections and messages."""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info(f"Received WebSocket message: {message}")
            
            # Handle different message types
            if message.get("type") == "query":
                await handle_query_message(websocket, message)
            elif message.get("type") == "ping":
                await websocket_manager.send_personal_message(
                    json.dumps({"type": "pong"}), websocket
                )
            else:
                await websocket_manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Unknown message type"}), 
                    websocket
                )
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

async def handle_query_message(websocket: WebSocket, message: Dict[str, Any]):
    """Handle query messages from WebSocket clients."""
    try:
        user_query = message.get("query", "").strip()
        
        if not user_query:
            await websocket_manager.send_personal_message(
                json.dumps({"type": "error", "message": "Query is required"}), 
                websocket
            )
            return
        
        # Send initial response
        await websocket_manager.send_personal_message(
            json.dumps({
                "type": "status", 
                "message": "Processing your query...",
                "status": "processing"
            }), 
            websocket
        )
        
        # Stream the query through the agent
        async for chunk in agent.stream_query(user_query):
            await websocket_manager.send_personal_message(
                json.dumps(chunk), 
                websocket
            )
        
        # Send completion message
        await websocket_manager.send_personal_message(
            json.dumps({
                "type": "status", 
                "message": "Query completed",
                "status": "completed"
            }), 
            websocket
        )
        
    except Exception as e:
        logger.error(f"Error handling query message: {e}")
        await websocket_manager.send_personal_message(
            json.dumps({
                "type": "error", 
                "message": f"Error processing query: {str(e)}"
            }), 
            websocket
        )
