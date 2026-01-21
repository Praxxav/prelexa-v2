from fastapi import APIRouter, Depends
from app.utils.dependencies import get_org_id
from app.services.meeting_lifecycle import start_live_meeting, stop_live_meeting
from app.documents.live_document_state import LIVE_DOCUMENT_STATE
from app.services.document_service import DocumentService

router = APIRouter()
document_service = DocumentService()

@router.post("/live")  
async def start_live_meeting_api(  
    payload: dict,
    org_id: str = Depends(get_org_id),
):
    meeting = await start_live_meeting(
        org_id=org_id,
        meet_url=payload.get("meet_url", "internal"),
    )

    return {
        "status": "Live meeting started",
        "meeting_id": meeting.meeting_id,
    }


@router.post("/live/end")
async def end_live_meeting_api(
    payload: dict,
    org_id: str = Depends(get_org_id),
):
    meeting_id = payload.get("meeting_id")
    title = payload.get("title", "Untitled Meeting")
    
    # 1. Stop lifecycle (mark as stopped)
    stop_live_meeting(meeting_id)

    # 2. Get State
    state = LIVE_DOCUMENT_STATE.get(meeting_id)
    if not state:
        # Depending on if we want to fail or just create empty doc
        state = {
            "transcript": "No transcript available.",
            "decisions": [],
            "action_items": [],
            "risks": []
        }
    
    # 3. Create Document
    doc = await document_service.create_live_meeting_document(org_id, title, state)

    # 4. Clear State
    if meeting_id in LIVE_DOCUMENT_STATE:
        del LIVE_DOCUMENT_STATE[meeting_id]

    return {
        "status": "Meeting ended and saved",
        "document_id": doc.id
    }
