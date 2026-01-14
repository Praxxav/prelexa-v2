import json
from typing import Any, Dict, Optional, List
from app.agent.base_agent import BaseAgent
from core.config import settings


class RiskAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="RiskAgent",
            role="Identify risks, blockers, or ambiguities",
            api_key=settings.GEMINI_API_KEY,
        )

    async def process(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> List[Dict]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You identify RISKS, BLOCKERS, or AMBIGUITIES in meetings.\n"
                    "Classify severity as low, medium, or high.\n"
                    "Return JSON in the format:\n"
                    "[{ \"risk\": \"\", \"severity\": \"low|medium|high\" }]"
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
