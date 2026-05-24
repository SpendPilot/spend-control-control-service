from __future__ import annotations

import os
from datetime import date

import psycopg
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main() -> None:
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://spendcontrol:spendcontrol@localhost:5432/spend_control",
    )
    sync_url = database_url.replace("+psycopg", "")
    with psycopg.connect(sync_url) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS control")
            cur.execute("CREATE SCHEMA IF NOT EXISTS expense")
            cur.execute("CREATE SCHEMA IF NOT EXISTS ai")

            cur.execute(
                """
                INSERT INTO expense.companies (id, name)
                VALUES (1, 'Northstar Dynamics')
                ON CONFLICT (id) DO NOTHING
                """
            )
            cur.execute(
                """
                INSERT INTO expense.departments (id, company_id, name, manager_email)
                VALUES
                  (1, 1, 'Engineering', 'manager@northstar.test'),
                  (2, 1, 'Operations', 'manager@northstar.test'),
                  (3, 1, 'Finance', 'finance@northstar.test')
                ON CONFLICT (id) DO NOTHING
                """
            )
            cur.execute(
                """
                INSERT INTO expense.budgets (id, company_id, department_id, month, allocated_amount, consumed_amount, warning_threshold_percent)
                VALUES
                  (1, 1, 1, %s, 15000, 6200, 85),
                  (2, 1, 2, %s, 22000, 19500, 85),
                  (3, 1, 3, %s, 12000, 8400, 80)
                ON CONFLICT (id) DO NOTHING
                """,
                [date.today().strftime("%Y-%m")] * 3,
            )

            cur.execute(
                """
                INSERT INTO control.roles (id, name, description)
                VALUES
                  (1, 'employee', 'Standard employee submitter'),
                  (2, 'manager', 'Department approver'),
                  (3, 'finance_admin', 'Finance administrator')
                ON CONFLICT (id) DO NOTHING
                """
            )

            password_hash = pwd_context.hash("Password123!")
            users = [
                (1, 1, 1, 1, "employee@northstar.test", "Avery Employee", password_hash),
                (2, 1, 2, 2, "manager@northstar.test", "Morgan Manager", password_hash),
                (3, 1, 3, 3, "finance@northstar.test", "Finley Finance", password_hash),
            ]
            for user in users:
                cur.execute(
                    """
                    INSERT INTO control.users (id, company_id, department_id, role_id, email, full_name, password_hash, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, true)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    user,
                )

            policies = [
                (
                    1,
                    "Receipt required above threshold",
                    "Claims above 75 must include a receipt.",
                    "receipt_threshold",
                    75,
                    None,
                    None,
                ),
                (
                    2,
                    "Travel cap",
                    "Single travel claim cap.",
                    "category_cap",
                    1200,
                    "travel",
                    None,
                ),
                (
                    3,
                    "Weekend restriction",
                    "Meals and entertainment on weekends require intervention.",
                    "weekend_restriction",
                    None,
                    None,
                    '{"categories":["meals","entertainment"]}',
                ),
            ]
            for policy in policies:
                cur.execute(
                    """
                    INSERT INTO control.policy_rules (id, name, description, rule_type, threshold_amount, category, config_json, active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, true)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    policy,
                )

            cur.execute(
                """
                INSERT INTO expense.expense_claims (
                  id, company_id, department_id, department_name, submitted_by_user_id, submitted_by_email,
                  title, merchant, category, amount, currency, expense_date, status, policy_status,
                  reimbursement_state, notes
                )
                VALUES
                  (1, 1, 1, 'Engineering', 1, 'employee@northstar.test', 'Client travel to Chicago', 'Atlas Air', 'travel', 480, 'USD', CURRENT_DATE - 5, 'under_review', 'warning', 'not_started', 'Quarterly client review'),
                  (2, 1, 2, 'Operations', 1, 'employee@northstar.test', 'Hotel near client site', 'Civic Hotel', 'travel', 310, 'USD', CURRENT_DATE - 3, 'submitted', 'failed', 'not_started', 'Late check-in after site visit'),
                  (3, 1, 2, 'Operations', 1, 'employee@northstar.test', 'Round-number team dinner', 'Harbor Restaurant', 'meals', 200, 'USD', CURRENT_DATE - 1, 'submitted', 'pending', 'not_started', 'Operations team dinner')
                ON CONFLICT (id) DO NOTHING
                """
            )
            cur.execute(
                """
                INSERT INTO expense.expense_items (id, claim_id, description, amount, category, expense_date)
                VALUES
                  (1, 1, 'Round-trip flight', 480, 'travel', CURRENT_DATE - 5),
                  (2, 2, 'Two-night stay', 310, 'travel', CURRENT_DATE - 3),
                  (3, 3, 'Team dinner', 200, 'meals', CURRENT_DATE - 1)
                ON CONFLICT (id) DO NOTHING
                """
            )
            cur.execute(
                """
                INSERT INTO expense.anomalies (id, claim_id, type, severity, message, status, metadata_json)
                VALUES
                  (1, 2, 'possible_duplicate', 'high', 'Possible duplicate claim detected with similar merchant and amount.', 'open', '{"matched_claim_id":1}'),
                  (2, 3, 'rounded_amount', 'medium', 'Rounded amount pattern detected on a higher-value claim.', 'open', '{"amount":200}')
                ON CONFLICT (id) DO NOTHING
                """
            )
            cur.execute(
                """
                INSERT INTO expense.audit_events (id, action, actor_email, target_type, target_id, summary)
                VALUES
                  (1, 'seed_claim_created', 'system@seed', 'expense_claim', '1', 'Seeded demo claim 1'),
                  (2, 'seed_claim_created', 'system@seed', 'expense_claim', '2', 'Seeded demo claim 2'),
                  (3, 'seed_claim_created', 'system@seed', 'expense_claim', '3', 'Seeded demo claim 3')
                ON CONFLICT (id) DO NOTHING
                """
            )
            cur.execute(
                """
                INSERT INTO control.approval_steps (id, claim_id, approver_user_id, decision)
                VALUES
                  (1, 1, 2, 'pending'),
                  (2, 2, 2, 'pending'),
                  (3, 3, 2, 'pending')
                ON CONFLICT (id) DO NOTHING
                """
            )
        conn.commit()

    print("Demo seed complete.")


if __name__ == "__main__":
    main()

