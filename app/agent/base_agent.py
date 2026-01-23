"""
Base Agent class for all multi-agent orchestration patterns.
Updated to use google-genai (official Gemini SDK).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import google.genai as genai
import asyncio
import time


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(
        self,
        name: str,
        role: str,
        api_key: str,
        model: str = "gemini-2.5-flash",
    ):
        self.name = name
        self.role = role
        self.model = model

        # New official Gemini client
        self.client = genai.Client(api_key=api_key)

        self.execution_time: float = 0.0
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

    @abstractmethod
    async def process(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> Any:
        """Process input data and return output."""
        pass

    async def _make_api_call(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        response_format: str = "text",
    ) -> str:
        """Make an async API call to Google Gemini and track metrics."""
        start_time = time.time()

        try:
            # Convert messages → Gemini content format
            contents: List[Dict] = []

            system_prompt = ""
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt += msg["content"] + "\n"
                elif msg["role"] == "user":
                    content = (
                        system_prompt + msg["content"]
                        if system_prompt
                        else msg["content"]
                    )
                    contents.append(
                        {
                            "role": "user",
                            "parts": [{"text": content}],
                        }
                    )
                    system_prompt = ""
                elif msg["role"] == "assistant":
                    contents.append(
                        {
                            "role": "model",
                            "parts": [{"text": msg["content"]}],
                        }
                    )

            # Generation config
            generation_config: Dict[str, Any] = {
                "temperature": temperature
            }

            if response_format == "json":
                generation_config["response_mime_type"] = "application/json"

            # Async Gemini call
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generation_config,
            )

            self.execution_time = time.time() - start_time

            # Token usage (available when enabled by API)
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                self.token_usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }

            return response.text

        except Exception as e:
            self.execution_time = time.time() - start_time
            raise RuntimeError(
                f"Gemini API call failed for agent '{self.name}': {str(e)}"
            )

    def get_metrics(self) -> Dict:
        """Get execution metrics for this agent."""
        return {
            "name": self.name,
            "role": self.role,
            "execution_time": round(self.execution_time, 3),
            "token_usage": self.token_usage,
        }


class SimpleAgent(BaseAgent):
    """A simple agent implementation for basic tasks."""

    def __init__(
        self,
        name: str,
        role: str,
        api_key: str,
        system_prompt: str,
        model: str = "gemini-2.5-flash",
    ):
        super().__init__(name, role, api_key, model)
        self.system_prompt = system_prompt

    async def process(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> Any:
        """Process input using the system prompt."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": str(input_data)},
        ]

        if context:
            messages.insert(
                1,
                {
                    "role": "system",
                    "content": f"Context: {context}",
                },
            )

        return await self._make_api_call(messages)
