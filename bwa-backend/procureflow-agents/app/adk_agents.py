import os

try:
    from google.adk import Agent
except Exception:  # pragma: no cover - keeps local deterministic mode resilient.
    Agent = None


def build_adk_agent(name: str, instruction: str):
    if Agent is None:
        return None
    return Agent(
        name=name,
        model=os.getenv("AGENT_MODEL", "gemini-flash-latest"),
        instruction=instruction,
    )


ADK_AGENT_DEFINITIONS = {
    "vendor_intake": build_adk_agent(
        "vendor_intake_agent",
        "Extract vendor proposal facts and return concise procurement JSON.",
    ),
    "contract_risk": build_adk_agent(
        "contract_risk_agent",
        "Review contract terms for procurement legal risk and negotiation points.",
    ),
    "security_review": build_adk_agent(
        "security_review_agent",
        "Assess security, privacy, and compliance risks from vendor proposal text.",
    ),
    "budget": build_adk_agent(
        "budget_agent",
        "Check procurement requests against department budgets and approval thresholds.",
    ),
    "approval": build_adk_agent(
        "approval_orchestrator_agent",
        "Combine procurement findings into an approval workflow and final decision.",
    ),
}
