from fastapi import APIRouter, Depends, HTTPException
from app.utils.dependencies import get_org_id
from app.documents.live_document_state import LIVE_DOCUMENT_STATE
from app.services.document_service import create_document_from_meeting
from app.services.live_meeting_service import RUNNING_MEETINGS
from datetime import datetime
from app.db import prisma
from app.schemas.meeting import EndMeetingPayload
from app.websockets.connection_manager import connection_manager

router = APIRouter()

@router.post("/live/end")
async def end_live_meeting(
    payload: EndMeetingPayload,
    org_id: str = Depends(get_org_id)
):
    meeting_id = payload.meeting_id
    title = payload.title or f"Meeting {meeting_id}"

    # 1. Retrieve State
    state = LIVE_DOCUMENT_STATE.get(meeting_id, {"transcript": "", "decisions": [], "action_items": [], "risks": []})
    
    # 2. Capture End Time
    ended_at = datetime.utcnow()
    # Mock start time if not tracked (e.g. 30 mins ago for demo, or just now)
    # In a real app, track `started_at` in `LIVE_DOCUMENT_STATE`.
    started_at = state.get("started_at", ended_at) 
    duration_seconds = int((ended_at - started_at).total_seconds())
    if duration_seconds < 0: duration_seconds = 0

    # 3. Create Document
    doc = await create_document_from_meeting(org_id, title, state)

    # Cleanup
    if meeting_id in LIVE_DOCUMENT_STATE:
        del LIVE_DOCUMENT_STATE[meeting_id]
        
    return {
        "status": "meeting ended",
        "document_id": doc.id,
    }
