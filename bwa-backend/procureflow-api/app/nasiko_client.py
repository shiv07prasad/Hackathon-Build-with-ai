from typing import Any

import httpx

from app.config import settings


class AgentClient:
    def __init__(self) -> None:
        self._timeout = httpx.Timeout(60.0)

    async def call(self, agent_name: str, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        if settings.use_nasiko:
            base_url = settings.nasiko_base_url.rstrip("/")
            url = f"{base_url}/agents/{agent_name}{endpoint}"
        else:
            base_url = settings.agent_base_url.rstrip("/")
            url = f"{base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
