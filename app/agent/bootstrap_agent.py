import httpx
import logging
import json
import re
import yaml
import google.genai as genai
from .templatizer import templatizer_agent
from core.config import settings


class WebBootstrapAgent:
    def __init__(self):
        self.api_key = settings.EXA_API_KEY
        self.base_url = "https://api.exa.ai/search"

        # Gemini client (official SDK)
        self.gemini_client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    async def fetch_public_examples(self, query: str):
        """Query exa.ai for legal document exemplars with full text content."""
        try:
            enhanced_query = f"{query} legal document template sample format"

            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": enhanced_query,
                        "numResults": 3,
                        "type": "neural",
                        "useAutoprompt": True,
                        "contents": {"text": True},
                    },
                )

                if response.status_code != 200:
                    logging.error(
                        f"Exa.ai API error: {response.status_code} - {response.text}"
                    )
                    return []

                data = response.json()
                results = []

                for item in data.get("results", []):
                    text_content = (
                        item.get("text")
                        or item.get("content")
                        or item.get("snippet")
                        or ""
                    )

                    if text_content:
                        results.append(
                            {
                                "title": item.get("title", "Untitled"),
                                "url": item.get("url", ""),
                                "text": text_content,
                            }
                        )

                logging.info(
                    f"✅ Exa.ai returned {len(results)} results with content"
                )
                return results

        except Exception as e:
            logging.error("❌ Exa.ai fetch error", exc_info=True)
            return []

    async def bootstrap_template(self, query: str):
        """
        Fetch exemplar from web and convert it into a structured template
        with YAML front-matter and extracted variables.
        """
        try:
            # Step 1: Fetch examples
            examples = await self.fetch_public_examples(query)
            if not examples:
                logging.warning("No examples found from Exa.ai")
                return None

            exemplar = examples[0]
            text = exemplar["text"]

            if not text or len(text.strip()) < 100:
                if len(examples) > 1:
                    exemplar = examples[1]
                    text = exemplar["text"]
                else:
                    return None

            logging.info(
                f"📄 Processing: {exemplar['title']} ({len(text)} chars)"
            )

            # Step 2: Templatize
            template_markdown = await templatizer_agent.process(text)

            if not template_markdown:
                logging.error("Templatizer returned empty output")
                return None

            # Step 3: Parse template
            template_data = self._parse_template_markdown(template_markdown)

            # Step 4: Ensure variables exist
            if not template_data.get("variables"):
                logging.warning(
                    "⚠️ No variables extracted — using aggressive fallback"
                )
                template_data = await self._aggressive_variable_extraction(
                    text,
                    template_markdown,
                    template_data,
                )

            return {
                "template_markdown": template_markdown,
                "full_markdown": template_markdown,
                "title": template_data.get("title")
                or f"Template: {exemplar['title'][:50]}",
                "file_description": template_data.get("file_description")
                or f"Sourced from web for: {query}",
                "jurisdiction": template_data.get("jurisdiction", ""),
                "doc_type": template_data.get("doc_type")
                or self._infer_doc_type(query),
                "similarity_tags": template_data.get("similarity_tags")
                or self._generate_tags(query),
                "source_url": exemplar["url"],
                "source_title": exemplar["title"],
                "variables": template_data.get("variables", []),
            }

        except Exception:
            logging.error("❌ Bootstrap template failed", exc_info=True)
            return None

    def _parse_template_markdown(self, markdown: str) -> dict:
        """Parse YAML front-matter from markdown."""
        try:
            if not markdown.strip().startswith("---"):
                return {"body": markdown, "variables": []}

            parts = markdown.split("---", 2)
            if len(parts) < 3:
                return {"body": markdown, "variables": []}

            yaml_str = parts[1].strip()
            body = parts[2].strip()

            metadata = yaml.safe_load(yaml_str) or {}

            return {
                "title": metadata.get("title", ""),
                "file_description": metadata.get("file_description", ""),
                "jurisdiction": metadata.get("jurisdiction", ""),
                "doc_type": metadata.get("doc_type", ""),
                "similarity_tags": metadata.get("similarity_tags", []),
                "variables": metadata.get("variables", []),
                "body": body,
            }

        except Exception as e:
            logging.error("Markdown parse failed", exc_info=True)
            return {"body": markdown, "variables": []}

    async def _aggressive_variable_extraction(
        self,
        original_text: str,
        template_markdown: str,
        existing_data: dict,
    ) -> dict:
        """
        Guaranteed variable extraction using Gemini (fallback).
        """
        try:
            prompt = f"""
Extract ALL variable fields from this legal document.

Look for:
- Names
- Dates
- Addresses
- Monetary amounts
- Case numbers
- Policy numbers
- Parties
- Deadlines

DOCUMENT:
{original_text[:3000]}

Return ONLY valid JSON array:

[
  {{
    "key": "party_name",
    "label": "Party Name",
    "description": "Name of the primary party",
    "example": "John Doe",
    "required": true,
    "type": "string"
  }}
]

STRICT:
- JSON only
- No markdown
- No explanations
"""

            response = await self.gemini_client.models.generate_content_async(
                model="gemini-1.5-flash",
                contents=[
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                generation_config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json",
                },
            )

            text = response.text.strip()

            if text.startswith("```"):
                text = re.sub(r"```(?:json)?", "", text)
                text = text.replace("```", "").strip()

            variables = json.loads(text)

            if isinstance(variables, list) and variables:
                existing_data["variables"] = variables
                logging.info(
                    f"✅ Aggressive extraction added {len(variables)} variables"
                )

            return existing_data

        except Exception:
            logging.error(
                "❌ Aggressive variable extraction failed", exc_info=True
            )
            return existing_data

    def _infer_doc_type(self, query: str) -> str:
        query_lower = query.lower()

        if any(w in query_lower for w in ["notice", "notification"]):
            return "legal_notice"
        if any(w in query_lower for w in ["contract", "agreement"]):
            return "contract"
        if any(w in query_lower for w in ["lease", "rent"]):
            return "lease_agreement"
        if any(w in query_lower for w in ["complaint", "petition"]):
            return "court_filing"

        return "legal_document"

    def _generate_tags(self, query: str) -> list:
        stop_words = {"a", "the", "in", "on", "for", "to", "of", "draft", "create"}
        words = query.lower().split()
        return [w for w in words if w not in stop_words and len(w) > 2][:5]


bootstrap_agent = WebBootstrapAgent()
