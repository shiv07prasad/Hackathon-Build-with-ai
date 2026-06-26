from typing import Any

from pydantic import BaseModel, Field


class AnalysisRecord(BaseModel):
    analysis_id: str
    status: str
    requester: str | None = None
    department: str | None = None
    estimated_amount: float | None = None
    filename: str
    extracted_text: str
    agent_results: dict[str, Any] = Field(default_factory=dict)
    final_decision: dict[str, Any] | None = None


class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    vendor: dict[str, Any]
    agent_results: dict[str, Any]
    risks: list[dict[str, Any]]
    required_approvals: list[str]
    workflow: list[dict[str, Any]]
    summary: str
