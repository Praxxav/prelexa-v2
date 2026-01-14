# backend/app/api/live_meeting_ws.py
from fastapi import APIRouter, WebSocket
from app.websocket.websocket_manager import connection_manager as manager

router = APIRouter()

@router.websocket("/live/ws")
async def live_meeting_ws(websocket: WebSocket):
    """
    WebSocket for LIVE MEETING updates (decisions, actions, risks).
    Auth via query param: ?orgId=xxx
    """
    org_id = websocket.query_params.get("orgId")

    if not org_id:
        # Policy violation / unauthorized
        await websocket.close(code=1008)
        return

    await manager.connect(org_id, websocket)

    try:
        while True:
            # keep connection alive
            await websocket.receive_text()
    except:
        manager.disconnect(org_id, websocket)
