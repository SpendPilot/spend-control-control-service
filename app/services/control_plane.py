from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.clients.ai_client import AIServiceClient
from app.clients.expense_client import ExpenseServiceClient
from app.models import ApprovalStep, PolicyRule, User
from app.schemas.ai import ChatRequest, ChatResponse, FinanceSummaryOut
from app.schemas.approvals import ApprovalDecision, ApprovalQueueItem
from app.schemas.auth import UserOut
from app.schemas.dashboard import DashboardOverview
from app.schemas.expenses import ClaimCreatePublic, ClaimOutPublic
from app.schemas.policy import PolicyRuleCreate, PolicyRuleOut, PolicyRuleUpdate
from app.services.policy_engine import evaluate_claim_policies

expense_client = ExpenseServiceClient()
ai_client = AIServiceClient()


def _claim_to_public(claim: dict) -> ClaimOutPublic:
    return ClaimOutPublic(**claim)


def _get_manager_for_department(db: Session, department_id: int) -> User | None:
    return (
        db.query(User)
        .join(User.role)
        .filter(User.department_id == department_id, User.role.has(name="manager"))
        .first()
    )


def _get_finance_admin(db: Session) -> User:
    admin = db.query(User).join(User.role).filter(User.role.has(name="finance_admin")).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Finance admin not configured")
    return admin


def _create_pending_step(db: Session, claim_id: int, approver_user_id: int) -> None:
    db.add(ApprovalStep(claim_id=claim_id, approver_user_id=approver_user_id, decision="pending"))
    db.commit()


def get_policies(db: Session) -> list[PolicyRuleOut]:
    return [PolicyRuleOut.model_validate(rule, from_attributes=True) for rule in db.query(PolicyRule).all()]


def create_policy_rule(db: Session, payload: PolicyRuleCreate) -> PolicyRuleOut:
    policy = PolicyRule(
        name=payload.name,
        description=payload.description,
        rule_type=payload.rule_type,
        threshold_amount=Decimal(str(payload.threshold_amount)) if payload.threshold_amount is not None else None,
        category=payload.category,
        config_json=payload.config_json,
        active=payload.active,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return PolicyRuleOut.model_validate(policy, from_attributes=True)


def patch_policy_rule(db: Session, policy_id: int, payload: PolicyRuleUpdate) -> PolicyRuleOut:
    policy = db.query(PolicyRule).filter(PolicyRule.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        if field == "threshold_amount":
            setattr(policy, field, Decimal(str(value)))
        else:
            setattr(policy, field, value)
    db.commit()
    db.refresh(policy)
    return PolicyRuleOut.model_validate(policy, from_attributes=True)


def submit_claim(db: Session, current_user: UserOut, payload: ClaimCreatePublic) -> ClaimOutPublic:
    claim = expense_client.create_claim(
        {
            **payload.model_dump(),
            "company_id": current_user.company_id,
            "department_id": current_user.department_id,
            "department_name": get_department_name(current_user.department_id),
            "submitted_by_user_id": current_user.id,
            "submitted_by_email": current_user.email,
        },
        actor_email=current_user.email,
    )
    policies = db.query(PolicyRule).all()
    policy_status, _ = evaluate_claim_policies(claim, policies, expense_client.get_budgets())
    claim = expense_client.patch_claim(
        claim["id"],
        {"policy_status": policy_status, "status": "under_review"},
        actor_email=current_user.email,
    )
    manager = _get_manager_for_department(db, current_user.department_id or 0) or _get_finance_admin(db)
    _create_pending_step(db, claim["id"], manager.id)
    return _claim_to_public(claim)


def get_my_claims(db: Session, current_user: UserOut) -> list[ClaimOutPublic]:
    params = None
    if current_user.role == "employee":
        params = {"submitted_by_user_id": current_user.id}
    elif current_user.role == "manager" and current_user.department_id is not None:
        params = {"department_id": current_user.department_id}
    claims = expense_client.list_claims(params=params)
    return [_claim_to_public(claim) for claim in claims]


def get_approval_queue(db: Session, current_user: UserOut) -> list[ApprovalQueueItem]:
    rows = (
        db.query(ApprovalStep)
        .filter(ApprovalStep.approver_user_id == current_user.id, ApprovalStep.decision == "pending")
        .order_by(ApprovalStep.created_at.asc())
        .all()
    )
    results: list[ApprovalQueueItem] = []
    for row in rows:
        claim = expense_client.get_claim(row.claim_id)
        results.append(
            ApprovalQueueItem(
                claim_id=row.claim_id,
                title=claim["title"],
                merchant=claim["merchant"],
                amount=claim["amount"],
                category=claim["category"],
                employee_email=claim["submitted_by_email"],
                submitted_at=claim["created_at"],
                status=claim["status"],
                decision=row.decision,
            )
        )
    return results


def record_approval_decision(
    db: Session, current_user: UserOut, claim_id: int, payload: ApprovalDecision
) -> ClaimOutPublic:
    step = (
        db.query(ApprovalStep)
        .filter(
            ApprovalStep.claim_id == claim_id,
            ApprovalStep.approver_user_id == current_user.id,
            ApprovalStep.decision == "pending",
        )
        .first()
    )
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval step not found")

    step.decision = payload.decision
    step.comment = payload.comment
    step.decided_at = datetime.utcnow()
    db.commit()

    if payload.decision == "rejected":
        claim = expense_client.patch_claim(claim_id, {"status": "rejected"}, actor_email=current_user.email)
        return _claim_to_public(claim)

    if current_user.role == "manager":
        finance_admin = _get_finance_admin(db)
        _create_pending_step(db, claim_id, finance_admin.id)
        claim = expense_client.patch_claim(claim_id, {"status": "under_review"}, actor_email=current_user.email)
        return _claim_to_public(claim)

    claim = expense_client.patch_claim(
        claim_id,
        {"status": "approved", "reimbursement_state": "scheduled"},
        actor_email=current_user.email,
    )
    return _claim_to_public(claim)


async def upload_claim_receipt(
    db: Session,
    current_user: UserOut,
    claim_id: int,
    file: UploadFile,
    corrected_merchant: str | None,
    corrected_amount: float | None,
    corrected_date: str | None,
) -> dict:
    receipt = await expense_client.upload_receipt(
        claim_id,
        file,
        actor_email=current_user.email,
        corrected_merchant=corrected_merchant,
        corrected_amount=corrected_amount,
        corrected_date=corrected_date,
    )
    claim = expense_client.get_claim(claim_id)
    policies = db.query(PolicyRule).all()
    policy_status, reasons = evaluate_claim_policies(claim, policies, expense_client.get_budgets())
    expense_client.patch_claim(claim_id, {"policy_status": policy_status}, actor_email=current_user.email)
    return {"receipt": receipt, "policy_status": policy_status, "policy_reasons": reasons}


def get_dashboard_overview(db: Session, current_user: UserOut) -> DashboardOverview:
    analytics = expense_client.get_analytics()
    weekly = get_finance_summary(db).model_dump()
    return DashboardOverview(
        metrics=analytics["metrics"],
        monthly_spend=analytics["monthly_spend"],
        category_spend=analytics["category_spend"],
        top_vendors=analytics["top_vendors"],
        weekly_summary=weekly,
    )


def get_budget_overview(db: Session, current_user: UserOut) -> list[dict]:
    budgets = expense_client.get_budgets()
    departments = {dept["id"]: dept["name"] for dept in expense_client.get_departments()}
    results: list[dict] = []
    for budget in budgets:
        burn = (budget["consumed_amount"] / budget["allocated_amount"] * 100) if budget["allocated_amount"] else 0
        results.append(
            {
                **budget,
                "department_name": departments.get(budget["department_id"], "Unknown"),
                "burn_percent": round(burn, 2),
            }
        )
    return results


def get_flagged_claims(db: Session, current_user: UserOut) -> list[dict]:
    anomalies = expense_client.get_anomalies()
    claims_cache = {claim["id"]: claim for claim in expense_client.list_claims()}
    enriched: list[dict] = []
    for anomaly in anomalies:
        claim = claims_cache.get(anomaly["claim_id"])
        explanation = ai_client.explain_anomaly(
            {
                "claim": claim,
                "anomaly": anomaly,
            }
        )
        enriched.append({"claim": claim, "anomaly": anomaly, "ai_explanation": explanation["explanation"]})
    return enriched


def get_audit_trail() -> list[dict]:
    return expense_client.get_audit_events()


def get_department_directory() -> list[dict]:
    return expense_client.get_departments()


def get_department_name(department_id: int | None) -> str:
    departments = expense_client.get_departments()
    for department in departments:
        if department["id"] == department_id:
            return department["name"]
    return "Unknown"


def get_finance_summary(db: Session) -> FinanceSummaryOut:
    analytics = expense_client.get_analytics()
    summary = ai_client.get_weekly_summary({"analytics": analytics})
    return FinanceSummaryOut(**summary)


def get_spend_chat_response(db: Session, current_user: UserOut, payload: ChatRequest) -> ChatResponse:
    answer = ai_client.chat(
        {
            "conversation_id": payload.conversation_id,
            "user_id": current_user.id,
            "question": payload.question,
            "role": current_user.role,
        }
    )
    return ChatResponse(**answer)

