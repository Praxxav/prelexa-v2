import json
from typing import Any, Dict, Optional, List
from app.agent.base_agent import BaseAgent
from core.config import settings


class ActionItemsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ActionItemsAgent",
            role="Extract action items with owners and deadlines",
            api_key=settings.GEMINI_API_KEY,
        )

    async def process(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> List[Dict]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You extract ACTION ITEMS from meetings.\n"
                    "Each action item must include task, owner, and deadline if available.\n"
                    "Return JSON in the format:\n"
                    "[{ \"task\": \"\", \"owner\": \"\", \"deadline\": \"\" }]"
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
