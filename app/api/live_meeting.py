from fastapi import APIRouter, Depends
from app.utils.dependencies import get_org_id
from app.services.meeting_lifecycle import start_live_meeting

router = APIRouter()

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
