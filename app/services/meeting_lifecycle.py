from datetime import datetime
from app.models.meeting import LiveMeeting

RUNNING_MEETINGS: dict[str, LiveMeeting] = {}

async def start_live_meeting(org_id: str, meet_url: str) -> LiveMeeting:
    meeting = LiveMeeting(
        meeting_id=f"meet-{int(datetime.utcnow().timestamp())}",
        org_id=org_id,
        meet_url=meet_url,
        started_at=datetime.utcnow(),
        status="running",
    )

    RUNNING_MEETINGS[meeting.meeting_id] = meeting
    return meeting


def stop_live_meeting(meeting_id: str) -> LiveMeeting | None:
    meeting = RUNNING_MEETINGS.pop(meeting_id, None)
    if meeting:
        meeting.ended_at = datetime.utcnow()
        meeting.status = "stopped"
    return meeting
