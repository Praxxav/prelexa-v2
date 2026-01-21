from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.websocket_manager import connection_manager
from app.services.live_meeting_service import process_live_text

router = APIRouter()
@router.websocket("/live/ws")
async def live_ws(websocket: WebSocket):
    meeting_id = websocket.query_params.get("meetingId")
    user_id = websocket.query_params.get("userId")
    user_name = websocket.query_params.get("userName") or "Anonymous"

    if not meeting_id or not user_id:
        await websocket.close(code=1008)
        return

    # Connect
    await connection_manager.connect(meeting_id, user_id, websocket, user_name)

    # 1. Send existing participants to the NEW user
    existing_users = connection_manager.get_participants(meeting_id)
    # Filter out self
    others = [u for u in existing_users if u["userId"] != user_id]
    
    await connection_manager.send_personal_message(
        {
            "type": "existing_participants",
            "payload": others
        },
        websocket
    )

    # 2. Notify others that a new user joined
    await connection_manager.broadcast(
        meeting_id,
        {
            "type": "user_joined",
            "payload": {"userId": user_id, "userName": user_name},
        },
        exclude_ws=websocket,
    )

    try:
        while True:
            # We accept both text (legacy transcript) and JSON (signaling)
            # websocket.receive_text() is easiest, then we try parse
            data = await websocket.receive_text()

            # Attempt to parse as JSON for signaling
            try:
                import json
                msg = json.loads(data)
                
                # Check for Signal type
                if isinstance(msg, dict) and "type" in msg:
                    msg_type = msg["type"]
                    
                    if msg_type == "signal":
                        # Relay signal to specific target
                        target = msg.get("target")
                        if target:
                            await connection_manager.send_to_user(
                                meeting_id, 
                                target, 
                                {
                                    "type": "signal",
                                    "sender": user_id,
                                    "senderName": user_name,
                                    "payload": msg.get("payload")
                                }
                            )
                        continue
                    
                    # You could add other JSON types here if needed

            except ValueError:
                pass # Not JSON, treat as transcript text

            # Treat as transcript if not signaling
            if data.strip() and not data.startswith("{"):
                await process_live_text(meeting_id, data)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print("Live WS error:", e)

    finally:
        connection_manager.disconnect(meeting_id, websocket)
        
        # Notify others user left
        await connection_manager.broadcast(
            meeting_id,
            {
                "type": "user_left",
                "payload": {"userId": user_id},
            }
        )
