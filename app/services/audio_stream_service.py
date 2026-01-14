# app/services/audio_stream_service.py
import asyncio
from app.services.live_meeting_service import process_live_text

async def simulate_live_audio(org_id: str):
    lines = [
        "We decided to go with PostgreSQL.",
        "Pranav will complete schema design by Friday.",
        "Security review is required before deployment."
    ]

    for line in lines:
        await process_live_text(org_id, line)
        await asyncio.sleep(5)
