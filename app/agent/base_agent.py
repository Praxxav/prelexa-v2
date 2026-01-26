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
            
            # Helper to process message content
            def format_parts(content_data: Any) -> List[Dict]:
                parts = []
                if isinstance(content_data, str):
                    parts.append({"text": content_data})
                elif isinstance(content_data, list):
                    # Handle list of mixed content (text + images)
                    for item in content_data:
                        if isinstance(item, str):
                             parts.append({"text": item})
                        elif isinstance(item, dict) and "mime_type" in item and "data" in item:
                             # Inline data (bytes)
                             parts.append({"inline_data": item})
                        elif isinstance(item, dict) and "file_uri" in item:
                             # File URI
                             parts.append({"file_data": {"file_uri": item["file_uri"], "mime_type": item.get("mime_type", "image/jpeg")}})
                return parts

            system_prompt = ""
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt += msg["content"] + "\n"
                elif msg["role"] == "user":
                    user_parts = format_parts(msg["content"])
                    
                    # Prepend system prompt to the first user message if it exists
                    if system_prompt:
                        # If the first part is text, prepend. If not, insert a new text part.
                        if user_parts and "text" in user_parts[0]:
                             user_parts[0]["text"] = system_prompt + user_parts[0]["text"]
                        else:
                             user_parts.insert(0, {"text": system_prompt})
                        system_prompt = "" # Clear after using
                    
                    contents.append({
                        "role": "user",
                        "parts": user_parts,
                    })
                elif msg["role"] == "assistant":
                     contents.append({
                        "role": "model",
                        "parts": format_parts(msg["content"]),
                    })

            # Generation config
            generation_config: Dict[str, Any] = {
                "temperature": temperature
            }

            if response_format == "json":
                generation_config["response_mime_type"] = "application/json"

            # Async Gemini call
            response = await self.client.aio.models.generate_content(
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
            {"role": "user", "content": input_data},
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
