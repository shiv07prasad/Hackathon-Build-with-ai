from typing import Any

from app.nasiko_client import AgentClient
from app.store import AnalysisStore


class ProcurementWorkflow:
    def __init__(self, store: AnalysisStore, agent_client: AgentClient) -> None:
        self._store = store
        self._agent_client = agent_client

    async def run(
        self,
        analysis_id: str,
        proposal_text: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        base_payload = {
            "analysis_id": analysis_id,
            "proposal_text": proposal_text,
            "metadata": metadata,
        }

        self._store.update(analysis_id, {"status": "intake_running"})
        intake = await self._agent_client.call(
            "vendor-intake-agent",
            "/intake/analyze",
            base_payload,
        )
        self._store.update(analysis_id, {"agent_results": {"intake": intake}, "status": "review_running"})

        enriched_payload = {**base_payload, "intake_result": intake}
        contract = await self._agent_client.call(
            "contract-risk-agent",
            "/contract/analyze",
            enriched_payload,
        )
        self._store.update(analysis_id, {"agent_results": {"contract": contract}})

        security = await self._agent_client.call(
            "security-review-agent",
            "/security/analyze",
            enriched_payload,
        )
        self._store.update(analysis_id, {"agent_results": {"security": security}})

        budget = await self._agent_client.call(
            "budget-agent",
            "/budget/analyze",
            enriched_payload,
        )
        self._store.update(analysis_id, {"agent_results": {"budget": budget}, "status": "approval_running"})

        approval_payload = {
            **base_payload,
            "intake_result": intake,
            "contract_result": contract,
            "security_result": security,
            "budget_result": budget,
        }
        approval = await self._agent_client.call(
            "approval-orchestrator-agent",
            "/approval/analyze",
            approval_payload,
        )

        agent_results = {
            "intake": intake,
            "contract": contract,
            "security": security,
            "budget": budget,
            "approval": approval,
        }
        final_payload = {
            "status": "completed",
            "agent_results": agent_results,
            "final_decision": approval,
        }
        self._store.update(analysis_id, final_payload)

        return {
            "analysis_id": analysis_id,
            "status": approval["decision"],
            "vendor": approval["vendor"],
            "agent_results": agent_results,
            "risks": approval["risks"],
            "required_approvals": approval["required_approvals"],
            "workflow": approval["workflow"],
            "summary": approval["summary"],
        }
