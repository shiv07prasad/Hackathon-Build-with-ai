from typing import Any

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    analysis_id: str
    proposal_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    intake_result: dict[str, Any] | None = None
    contract_result: dict[str, Any] | None = None
    security_result: dict[str, Any] | None = None
    budget_result: dict[str, Any] | None = None
