from fastapi import FastAPI

from app.agents import (
    analyze_approval,
    analyze_budget,
    analyze_contract,
    analyze_intake,
    analyze_security,
)
from app.adk_agents import ADK_AGENT_DEFINITIONS
from app.models import AgentRequest

app = FastAPI(title="ProcureFlow ADK Agents", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "service": "procureflow-agents",
        "adk_agents_loaded": [name for name, agent in ADK_AGENT_DEFINITIONS.items() if agent is not None],
    }


@app.post("/intake/analyze")
async def intake(request: AgentRequest) -> dict:
    return analyze_intake(request)


@app.post("/contract/analyze")
async def contract(request: AgentRequest) -> dict:
    return analyze_contract(request)


@app.post("/security/analyze")
async def security(request: AgentRequest) -> dict:
    return analyze_security(request)


@app.post("/budget/analyze")
async def budget(request: AgentRequest) -> dict:
    return analyze_budget(request)


@app.post("/approval/analyze")
async def approval(request: AgentRequest) -> dict:
    return analyze_approval(request)
