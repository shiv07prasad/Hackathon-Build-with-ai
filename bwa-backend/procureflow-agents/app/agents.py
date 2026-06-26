from pathlib import Path
from typing import Any

from app.helpers import DEPARTMENT_BUDGETS, FINANCE_APPROVAL_THRESHOLD, first_match, has_any, infer_amount
from app.llm import generate_json
from app.models import AgentRequest


def analyze_intake(request: AgentRequest) -> dict[str, Any]:
    fallback = _analyze_intake_rules(request)
    return _with_llm_fallback(
        "Extract vendor procurement intake fields from the proposal text. Return JSON with exactly these keys: vendor, service, department, annual_cost, billing, contract_term, renewal_date, missing_fields. annual_cost must be a number or null. missing_fields must be a list.",
        request,
        fallback,
    )


def _analyze_intake_rules(request: AgentRequest) -> dict[str, Any]:
    text = request.proposal_text
    metadata = request.metadata
    vendor = _infer_vendor(text, metadata)
    service = first_match(
        [
            r"(?:service|product|solution)[:\s]+([A-Za-z0-9 &.,-]+)",
            r"for\s+([A-Za-z0-9 &.,-]+ SaaS)",
        ],
        text,
    ) or "Vendor service"
    department = metadata.get("department") or first_match([r"department[:\s]+([A-Za-z &-]+)"], text)
    annual_cost = infer_amount(text, metadata)
    contract_term = first_match([r"(?:term|contract term)[:\s]+([A-Za-z0-9 ,.-]+)"], text) or "12 months"
    renewal_date = first_match([r"(?:renewal date|renews on)[:\s]+([A-Za-z0-9 ,.-]+)"], text)

    missing_fields = []
    if not department:
        missing_fields.append("department")
    if annual_cost is None:
        missing_fields.append("annual_cost")

    return {
        "vendor": vendor,
        "service": service,
        "department": department or "Unknown",
        "annual_cost": annual_cost,
        "billing": "annual" if has_any(text, ["annual", "yearly"]) else "unknown",
        "contract_term": contract_term,
        "renewal_date": renewal_date,
        "missing_fields": missing_fields,
    }


def _infer_vendor(text: str, metadata: dict[str, Any]) -> str:
    vendor = first_match(
        [
            r"(?:^|\n)\s*([A-Z][A-Za-z0-9 &.,-]+?)\s+(?:Vendor Proposal|SaaS Proposal|Subscription Proposal|Proposal)(?:\n|$)",
            r"(?:vendor|supplier|company)(?:\s+name)?\s*[:\-]\s*([^\n\r]+)",
            r"proposal from\s+([A-Za-z0-9 &.,-]+)",
        ],
        text,
    )
    vendor = _clean_vendor_name(vendor)
    if vendor:
        return vendor

    filename = str(metadata.get("filename") or "")
    stem = Path(filename).stem.replace("_", " ").replace("-", " ")
    for word in ["vendor", "proposal", "saas", "subscription", "contract", "agreement", "pdf"]:
        stem = stem.replace(word, " ").replace(word.title(), " ")
    vendor = " ".join(stem.split()).title()
    return vendor or "Unknown Vendor"


def _clean_vendor_name(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = " ".join(value.replace(":", " ").split())
    for suffix in ["Vendor Proposal", "SaaS Proposal", "Subscription Proposal", "Proposal"]:
        if cleaned.lower().endswith(suffix.lower()):
            cleaned = cleaned[: -len(suffix)].strip()
    if cleaned.lower() in {"vendor", "proposal", "vendor proposal", "supplier", "company"}:
        return None
    return cleaned or None


def analyze_contract(request: AgentRequest) -> dict[str, Any]:
    fallback = _analyze_contract_rules(request)
    return _with_llm_fallback(
        "Review the proposal/contract text for legal and commercial contract risk. Return JSON with exactly these keys: risk_level, issues, negotiation_points, recommendation. risk_level must be low, medium, or high. issues and negotiation_points must be lists.",
        request,
        fallback,
    )


def _analyze_contract_rules(request: AgentRequest) -> dict[str, Any]:
    text = request.proposal_text
    issues = []
    negotiation_points = []

    if has_any(text, ["auto-renew", "automatic renewal", "automatically renew"]):
        issues.append("Auto-renewal clause detected")
        negotiation_points.append("Remove auto-renewal or require explicit renewal approval")
    if has_any(text, ["60 days", "sixty days"]):
        issues.append("Cancellation may require 60 days notice")
        negotiation_points.append("Reduce cancellation notice period to 30 days")
    if has_any(text, ["liability capped", "liability cap", "three months", "3 months"]):
        issues.append("Liability cap may be too low")
        negotiation_points.append("Increase liability cap to at least 12 months of fees")
    if has_any(text, ["no service credits", "no sla", "best effort"]):
        issues.append("SLA protections may be weak")
        negotiation_points.append("Add uptime SLA and service credits")

    risk_level = "high" if len(issues) >= 2 else "medium" if issues else "low"
    return {
        "risk_level": risk_level,
        "issues": issues,
        "negotiation_points": negotiation_points,
        "recommendation": "Legal review required" if risk_level in {"medium", "high"} else "No legal blocker found",
    }


def analyze_security(request: AgentRequest) -> dict[str, Any]:
    fallback = _analyze_security_rules(request)
    return _with_llm_fallback(
        "Assess vendor security, privacy, and compliance risk from the proposal text. Return JSON with exactly these keys: risk_level, handles_customer_data, missing_documents, recommendation. risk_level must be low, medium, or high. handles_customer_data must be boolean. missing_documents must be a list.",
        request,
        fallback,
    )


def _analyze_security_rules(request: AgentRequest) -> dict[str, Any]:
    text = request.proposal_text
    handles_customer_data = has_any(text, ["customer data", "personal data", "pii", "crm data"])
    missing_documents = []
    if not has_any(text, ["soc2", "soc 2", "soc type ii"]):
        missing_documents.append("SOC2 Type II")
    if handles_customer_data and not has_any(text, ["dpa", "data processing agreement"]):
        missing_documents.append("DPA")
    if handles_customer_data and not has_any(text, ["gdpr"]):
        missing_documents.append("GDPR position")

    risk_level = "high" if handles_customer_data and len(missing_documents) >= 2 else "medium" if missing_documents else "low"
    return {
        "risk_level": risk_level,
        "handles_customer_data": handles_customer_data,
        "missing_documents": missing_documents,
        "recommendation": "Security review required" if missing_documents else "Security evidence appears sufficient",
    }


def analyze_budget(request: AgentRequest) -> dict[str, Any]:
    fallback = _analyze_budget_rules(request)
    return _with_llm_fallback(
        "Check the purchase against the provided mock procurement budget policy. Return JSON with exactly these keys: department, budget_category, budget_remaining, requested_amount, within_budget, finance_approval_required, reason. Use the budget context exactly; do not invent a different budget.",
        request,
        fallback,
        extra_context={"department_budgets": DEPARTMENT_BUDGETS, "finance_approval_threshold": FINANCE_APPROVAL_THRESHOLD},
    )


def _analyze_budget_rules(request: AgentRequest) -> dict[str, Any]:
    intake = request.intake_result or {}
    department = str(intake.get("department") or request.metadata.get("department") or "Unknown")
    amount = intake.get("annual_cost") or infer_amount(request.proposal_text, request.metadata) or 0
    budget = DEPARTMENT_BUDGETS.get(department.lower(), {"remaining": 0, "category": "Unknown"})
    remaining = budget["remaining"]
    within_budget = amount <= remaining
    finance_required = amount >= FINANCE_APPROVAL_THRESHOLD

    return {
        "department": department,
        "budget_category": budget["category"],
        "budget_remaining": remaining,
        "requested_amount": amount,
        "within_budget": within_budget,
        "finance_approval_required": finance_required,
        "reason": "Purchase exceeds approval threshold" if finance_required else "Below finance approval threshold",
    }


def analyze_approval(request: AgentRequest) -> dict[str, Any]:
    fallback = _analyze_approval_rules(request)
    return _with_llm_fallback(
        "Combine procurement agent outputs into the final approval package. Return JSON with exactly these keys: decision, vendor, risks, required_approvals, workflow, summary, negotiation_points. decision should be conditional_approval, needs_review, blocked_budget, or approved. risks must be a list of objects with type, severity, message. workflow must be a list of objects with step, status, reason.",
        request,
        fallback,
    )


def _analyze_approval_rules(request: AgentRequest) -> dict[str, Any]:
    intake = request.intake_result or {}
    contract = request.contract_result or {}
    security = request.security_result or {}
    budget = request.budget_result or {}

    risks = []
    required_approvals = []
    workflow = []

    if contract.get("risk_level") in {"medium", "high"}:
        required_approvals.append("Legal")
        for issue in contract.get("issues", []):
            risks.append({"type": "contract", "severity": contract["risk_level"], "message": issue})
        workflow.append(
            {
                "step": "Legal Review",
                "status": "required",
                "reason": contract.get("recommendation", "Contract risk requires legal review"),
            }
        )

    if security.get("risk_level") in {"medium", "high"}:
        required_approvals.append("Security")
        for document in security.get("missing_documents", []):
            risks.append({"type": "security", "severity": security["risk_level"], "message": f"{document} missing"})
        workflow.append(
            {
                "step": "Security Review",
                "status": "required",
                "reason": security.get("recommendation", "Security evidence required"),
            }
        )

    if budget.get("finance_approval_required") or not budget.get("within_budget", False):
        required_approvals.append("Finance")
        workflow.append(
            {
                "step": "Finance Approval",
                "status": "required",
                "reason": budget.get("reason", "Finance approval required"),
            }
        )

    if not required_approvals:
        workflow.append({"step": "Auto Approval", "status": "approved", "reason": "No blocking risks detected"})

    decision = "conditional_approval" if required_approvals and budget.get("within_budget", False) else "needs_review"
    if not budget.get("within_budget", False):
        decision = "blocked_budget"
        risks.append({"type": "budget", "severity": "high", "message": "Requested amount exceeds remaining budget"})

    return {
        "decision": decision,
        "vendor": {
            "name": intake.get("vendor", "Unknown Vendor"),
            "service": intake.get("service", "Vendor service"),
            "department": intake.get("department", "Unknown"),
            "annual_cost": intake.get("annual_cost"),
        },
        "risks": risks,
        "required_approvals": list(dict.fromkeys(required_approvals)),
        "workflow": workflow,
        "summary": _summary(decision, required_approvals),
        "negotiation_points": contract.get("negotiation_points", []),
    }


def _summary(decision: str, required_approvals: list[str]) -> str:
    if decision == "blocked_budget":
        return "Do not proceed until budget owner or finance resolves the budget gap."
    if required_approvals:
        return f"Proceed only after {', '.join(required_approvals)} approval is completed."
    return "Request can proceed with standard procurement processing."


def _with_llm_fallback(
    instruction: str,
    request: AgentRequest,
    fallback: dict[str, Any],
    extra_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "analysis_id": request.analysis_id,
        "proposal_text": request.proposal_text,
        "metadata": request.metadata,
        "intake_result": request.intake_result,
        "contract_result": request.contract_result,
        "security_result": request.security_result,
        "budget_result": request.budget_result,
        "fallback_shape": fallback,
        "extra_context": extra_context or {},
    }
    try:
        result = generate_json(instruction, payload)
        return _merge_with_fallback(result, fallback)
    except Exception as error:
        return {**fallback, "llm_used": False, "llm_error": str(error)}


def _merge_with_fallback(result: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    merged = {**fallback, **result}
    merged["llm_used"] = True
    return merged
