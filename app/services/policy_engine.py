from __future__ import annotations

from datetime import datetime

from app.core.config import get_settings
from app.models import PolicyRule


def evaluate_claim_policies(claim: dict, policies: list[PolicyRule], budgets: list[dict]) -> tuple[str, list[str]]:
    settings = get_settings()
    outcomes: list[str] = []
    has_failure = False
    has_warning = False

    expense_date = datetime.fromisoformat(str(claim["expense_date"]))
    receipts = claim.get("receipts", [])

    if claim["amount"] > settings.receipt_required_threshold and not receipts:
        has_failure = True
        outcomes.append("Receipt is required for claims above the configured threshold.")

    for rule in policies:
        if not rule.active:
            continue
        if rule.rule_type == "category_cap" and rule.category == claim["category"] and rule.threshold_amount:
            if claim["amount"] > float(rule.threshold_amount):
                has_failure = True
                outcomes.append(
                    f"Category cap exceeded for {claim['category']} against the {float(rule.threshold_amount):.2f} limit."
                )
        if rule.rule_type == "weekend_restriction":
            restricted = set((rule.config_json or {}).get("categories", []))
            if claim["category"] in restricted and expense_date.weekday() >= 5:
                has_failure = True
                outcomes.append(f"Weekend spend is restricted for {claim['category']} claims.")

    for budget in budgets:
        if budget["department_id"] == claim["department_id"] and budget["month"] == expense_date.strftime("%Y-%m"):
            burn = (budget["consumed_amount"] / budget["allocated_amount"] * 100) if budget["allocated_amount"] else 0
            if burn >= budget["warning_threshold_percent"]:
                has_warning = True
                outcomes.append(f"Department budget burn is elevated at {burn:.1f}% for the current month.")

    if has_failure:
        return "failed", outcomes
    if has_warning:
        return "warning", outcomes
    return "passed", outcomes or ["Claim passed deterministic policy checks."]

