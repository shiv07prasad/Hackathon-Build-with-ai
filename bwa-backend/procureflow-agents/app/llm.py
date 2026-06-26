import json
import os
import re
from typing import Any

from google import genai
from google.genai import types


_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() == "true"
        _client = genai.Client(
            vertexai=use_vertex,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    return _client


def generate_json(instruction: str, payload: dict[str, Any]) -> dict[str, Any]:
    model = os.getenv("AGENT_MODEL", "gemini-2.0-flash-001")
    prompt = f"""
You are an enterprise procurement agent.

Task:
{instruction}

Return only valid JSON. Do not wrap it in Markdown.

Input JSON:
{json.dumps(payload, ensure_ascii=False)}
""".strip()

    response = get_client().models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )
    return _parse_json(response.text or "")


def _parse_json(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("Gemini did not return a JSON object.")

    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Gemini JSON response was not an object.")
    return parsed
