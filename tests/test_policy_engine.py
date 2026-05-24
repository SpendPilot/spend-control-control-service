from types import SimpleNamespace

from app.services.policy_engine import evaluate_claim_policies


def test_policy_engine_fails_without_receipt_and_warns_on_budget():
    claim = {
        "amount": 150.0,
        "category": "travel",
        "expense_date": "2026-05-24",
        "department_id": 2,
        "receipts": [],
    }
    policies = [
        SimpleNamespace(active=True, rule_type="weekend_restriction", category=None, threshold_amount=None, config_json={"categories": ["travel"]}),
        SimpleNamespace(active=True, rule_type="category_cap", category="travel", threshold_amount=100.0, config_json=None),
    ]
    budgets = [
        {
            "department_id": 2,
            "month": "2026-05",
            "allocated_amount": 1000.0,
            "consumed_amount": 900.0,
            "warning_threshold_percent": 85.0,
        }
    ]

    status, reasons = evaluate_claim_policies(claim, policies, budgets)

    assert status == "failed"
    assert len(reasons) >= 2

