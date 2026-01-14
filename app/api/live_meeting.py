# app/api/live_meeting.py
from fastapi import APIRouter, Depends
from app.utils.dependencies import get_org_id
from app.services.live_meeting_service import start_live_meeting

router = APIRouter()

@router.post("/live/google-meet/start")
async def start_google_meet(
    payload: dict,
    org_id: str = Depends(get_org_id)
):
    meeting = await start_live_meeting(
        org_id=org_id,
        meet_url=payload["meet_url"]
    )
    return {
        "status": "Google Meet AI started",
        "meeting_id": meeting.meeting_id
    }
