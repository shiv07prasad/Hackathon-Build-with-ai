import re
from typing import Any


DEPARTMENT_BUDGETS = {
    "sales": {"remaining": 52000, "category": "Software"},
    "marketing": {"remaining": 30000, "category": "Software"},
    "engineering": {"remaining": 80000, "category": "Software"},
    "hr": {"remaining": 20000, "category": "Software"},
}

FINANCE_APPROVAL_THRESHOLD = 25000


def money_to_float(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.replace(",", "").replace("$", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def first_match(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def infer_amount(text: str, metadata: dict[str, Any]) -> float | None:
    if metadata.get("estimated_amount") is not None:
        return float(metadata["estimated_amount"])
    amount = first_match(
        [
            r"(?:annual cost|annual fee|total annual|contract value|amount)[:\s$]+([\d,]+(?:\.\d{2})?)",
            r"\$([\d,]+(?:\.\d{2})?)",
        ],
        text,
    )
    return money_to_float(amount)


def has_any(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)
