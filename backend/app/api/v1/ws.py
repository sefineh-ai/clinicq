import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.events import ws_manager
from app.core.security import decode_token

logger = logging.getLogger("clinicq.ws")
router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/queue")
async def websocket_queue_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None),
    doctor_id: int | None = Query(None),
):
    """
    Real-time WebSocket endpoint for queue and appointment updates.
    Open screens (Doctor desk, Receptionist console, Waiting room display)
    receive immediate push updates on:
      - Patient check-in (joins queue)
      - Patient called to consultation room
      - Consultation started / completed
      - New bookings and cancellations
      - Evening no-show sweep
    """
    # Accept connection
    client_id = await ws_manager.connect(websocket)
    logger.info(f"WebSocket client {client_id} connected (doctor_id={doctor_id})")

    # If doctor_id is specified, subscribe to their specific channel
    if doctor_id:
        ws_manager.subscribe_to_topic(websocket, f"doctor:{doctor_id}")

    try:
        # Send initial welcome and connection confirmation
        await websocket.send_text(
            json.dumps({
                "event": "CONNECTED",
                "client_id": client_id,
                "message": "Connected to ClinicQ live queue stream",
                "doctor_id": doctor_id,
            })
        )

        while True:
            # Keep connection alive, listen for ping or subscribe messages from client
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "ping":
                    await websocket.send_text(json.dumps({"event": "pong"}))
                elif msg.get("action") == "subscribe" and msg.get("topic"):
                    ws_manager.subscribe_to_topic(websocket, msg["topic"])
                    await websocket.send_text(
                        json.dumps({"event": "SUBSCRIBED", "topic": msg["topic"]})
                    )
            except Exception:
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.warning(f"WebSocket error for client {client_id}: {e}")
        ws_manager.disconnect(websocket)
