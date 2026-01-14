import asyncio
import threading
from datetime import datetime

from app.documents.live_document_state import LIVE_DOCUMENT_STATE
from app.websocket.websocket_manager import connection_manager
from app.agent.decisions_agent import DecisionsAgent
from app.agent.action_items_agent import ActionItemsAgent
from app.agent.risk_agent import RiskAgent
from app.models.meeting import LiveMeeting
from app.services.stt_service import stream_transcript

# In-memory running meetings
RUNNING_MEETINGS = {}


async def process_live_text(org_id: str, text: str):
    """
    Process one finalized speech chunk.
    """
    state = LIVE_DOCUMENT_STATE.setdefault(
        org_id,
        {
            "transcript": "",
            "decisions": [],
            "action_items": [],
            "risks": [],
        },
    )

    state["transcript"] += " " + text

    decisions_agent = DecisionsAgent()
    actions_agent = ActionItemsAgent()
    risks_agent = RiskAgent()

    decisions, actions, risks = await asyncio.gather(
        decisions_agent.process(text),
        actions_agent.process(text),
        risks_agent.process(text),
    )

    if decisions:
        state["decisions"].extend(decisions)

    if actions:
        state["action_items"].extend(actions)

    if risks:
        state["risks"].extend(risks)

    await connection_manager.broadcast(
        org_id,
        {
            "type": "live_update",
            "payload": state,
        },
    )


def start_stt_listener(org_id: str, loop: asyncio.AbstractEventLoop):
    """
    Runs Google STT (blocking) in a background thread.
    Bridges sync STT → async agents safely.
    """
    try:
        for text in stream_transcript():
            if not text or not text.strip():
                continue

            print("[STT]", text)

            asyncio.run_coroutine_threadsafe(
                process_live_text(org_id, text),
                loop,
            )
    except Exception as e:
        print("STT listener crashed:", e)


async def start_live_meeting(org_id: str, meet_url: str) -> LiveMeeting:
    """
    Start a live meeting with REAL speech-to-text.
    """
    meeting = LiveMeeting(
        meeting_id=f"meet-{datetime.utcnow().timestamp()}",
        org_id=org_id,
        meet_url=meet_url,
        started_at=datetime.utcnow(),
        status="running",
    )

    RUNNING_MEETINGS[meeting.meeting_id] = meeting

    # Get current event loop (FastAPI loop)
    loop = asyncio.get_running_loop()

    # Start STT in background thread
    threading.Thread(
        target=start_stt_listener,
        args=(org_id, loop),
        daemon=True,
    ).start()

    return meeting
