from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LiveMeeting(BaseModel):
    meeting_id: str
    org_id: str
    meet_url: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str  # running | stopped
