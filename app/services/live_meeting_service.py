import asyncio
from datetime import datetime

from app.documents.live_document_state import LIVE_DOCUMENT_STATE
from app.websocket.websocket_manager import connection_manager
from app.agent.decisions_agent import DecisionsAgent
from app.agent.action_items_agent import ActionItemsAgent
from app.agent.risk_agent import RiskAgent
from app.models.meeting import LiveMeeting

RUNNING_MEETINGS = {}


async def process_live_text(meeting_id: str, text: str):
    """
    Processes live text chunks coming from browser STT.
    """

    state = LIVE_DOCUMENT_STATE.setdefault(
        meeting_id,
        {
            "transcript": "",
            "decisions": [],
            "action_items": [],
            "risks": [],
        },
    )

    state["transcript"] += " " + text

    # 1. Update Transcript & Broadcast Immediately
    state["transcript"] += " " + text
    
    await connection_manager.broadcast(
        meeting_id,
        {
            "type": "live_update",
            "payload": state,
        },
        exclude_ws=None 
    )

    # 2. Run AI Agents in parallel
    decisions_agent = DecisionsAgent()
    actions_agent = ActionItemsAgent()
    risks_agent = RiskAgent()

    # We use gathered results to update state
    decisions, actions, risks = await asyncio.gather(
        decisions_agent.process(text),
        actions_agent.process(text),
        risks_agent.process(text),
    )

    has_changes = False

    if decisions:
        state["decisions"].extend(decisions)
        has_changes = True

    if actions:
        state["action_items"].extend(actions)
        has_changes = True

    if risks:
        state["risks"].extend(risks)
        has_changes = True
        
    # 3. If AI found something, broadcast again
    if has_changes:
        await connection_manager.broadcast(
            meeting_id,
            {
                "type": "live_update",
                "payload": state,
            },
            exclude_ws=None 
        )
