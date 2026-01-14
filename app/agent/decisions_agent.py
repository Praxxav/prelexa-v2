import json
from typing import Any, Dict, Optional, List
from app.agent.base_agent import BaseAgent
from core.config import settings


class DecisionsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="DecisionsAgent",
            role="Extract final decisions from meetings",
            api_key=settings.GEMINI_API_KEY,
        )

    async def process(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> List[str]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You extract ONLY FINAL, CONFIRMED decisions from meetings.\n"
                    "Ignore discussions, ideas, or open questions.\n"
                    "Return a JSON array of strings."
                ),
            },
            {
                "role": "user",
                "content": str(input_data),
            },
        ]

        output = await self._make_api_call(
            messages,
            response_format="json",
        )

        try:
            return json.loads(output)
        except Exception:
            return []
