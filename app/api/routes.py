from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ai import ChatRequest, ChatResponse, FinanceSummaryOut
from app.schemas.approvals import ApprovalDecision, ApprovalQueueItem
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.schemas.dashboard import DashboardOverview
from app.schemas.expenses import ClaimCreatePublic, ClaimOutPublic, ClaimUpdatePublic
from app.schemas.policy import PolicyRuleCreate, PolicyRuleOut, PolicyRuleUpdate
from app.services.auth import get_current_user, login_user, require_roles
from app.services.control_plane import (
    create_policy_rule,
    get_approval_queue,
    get_audit_trail,
    get_budget_overview,
    get_dashboard_overview,
    get_department_directory,
    get_finance_summary,
    get_flagged_claims,
    get_my_claims,
    get_policies,
    get_spend_chat_response,
    patch_policy_rule,
    record_approval_decision,
    submit_claim,
    upload_claim_receipt,
)
from spend_control_shared.responses import APIEnvelope, HealthResponse

router = APIRouter()
api = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        service="control-service",
        checks={"auth": "ready", "orchestration": "ready"},
    )


@api.post("/auth/login", response_model=APIEnvelope[TokenResponse])
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> APIEnvelope[TokenResponse]:
    return APIEnvelope(data=login_user(db, payload))


@api.get("/auth/me", response_model=APIEnvelope[UserOut])
def me(current_user: Annotated[UserOut, Depends(get_current_user)]) -> APIEnvelope[UserOut]:
    return APIEnvelope(data=current_user)


@api.get("/dashboard/overview", response_model=APIEnvelope[DashboardOverview])
def dashboard(
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(get_current_user)] = None,
) -> APIEnvelope[DashboardOverview]:
    assert current_user is not None
    return APIEnvelope(data=get_dashboard_overview(db, current_user))


@api.get("/expenses", response_model=APIEnvelope[list[ClaimOutPublic]])
def list_expenses(
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(get_current_user)] = None,
) -> APIEnvelope[list[ClaimOutPublic]]:
    assert current_user is not None
    return APIEnvelope(data=get_my_claims(db, current_user))


@api.post("/expenses", response_model=APIEnvelope[ClaimOutPublic])
def submit_expense(
    payload: ClaimCreatePublic,
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(require_roles("employee", "manager", "finance_admin"))] = None,
) -> APIEnvelope[ClaimOutPublic]:
    assert current_user is not None
    return APIEnvelope(data=submit_claim(db, current_user, payload))


@api.patch("/expenses/{claim_id}", response_model=APIEnvelope[ClaimOutPublic])
def update_expense(
    claim_id: int,
    payload: ClaimUpdatePublic,
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(require_roles("manager", "finance_admin"))] = None,
) -> APIEnvelope[ClaimOutPublic]:
    assert current_user is not None
    return APIEnvelope(data=record_approval_decision(db, current_user, claim_id, ApprovalDecision(decision="approved", comment=payload.notes or "Updated")))


@api.post("/expenses/{claim_id}/receipts", response_model=APIEnvelope[dict])
async def upload_receipt(
    claim_id: int,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    corrected_merchant: str | None = Form(default=None),
    corrected_amount: float | None = Form(default=None),
    corrected_date: str | None = Form(default=None),
    current_user: Annotated[UserOut, Depends(get_current_user)] = None,
) -> APIEnvelope[dict]:
    assert current_user is not None
    return APIEnvelope(
        data=await upload_claim_receipt(
            db,
            current_user,
            claim_id,
            file,
            corrected_merchant=corrected_merchant,
            corrected_amount=corrected_amount,
            corrected_date=corrected_date,
        )
    )


@api.get("/approvals/pending", response_model=APIEnvelope[list[ApprovalQueueItem]])
def approvals(
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(require_roles("manager", "finance_admin"))] = None,
) -> APIEnvelope[list[ApprovalQueueItem]]:
    assert current_user is not None
    return APIEnvelope(data=get_approval_queue(db, current_user))


@api.post("/approvals/{claim_id}/decision", response_model=APIEnvelope[ClaimOutPublic])
def decide_approval(
    claim_id: int,
    payload: ApprovalDecision,
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(require_roles("manager", "finance_admin"))] = None,
) -> APIEnvelope[ClaimOutPublic]:
    assert current_user is not None
    return APIEnvelope(data=record_approval_decision(db, current_user, claim_id, payload))


@api.get("/policies", response_model=APIEnvelope[list[PolicyRuleOut]])
def policies(
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(require_roles("manager", "finance_admin"))] = None,
) -> APIEnvelope[list[PolicyRuleOut]]:
    assert current_user is not None
    return APIEnvelope(data=get_policies(db))


@api.post("/policies", response_model=APIEnvelope[PolicyRuleOut])
def create_policy(
    payload: PolicyRuleCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(require_roles("finance_admin"))] = None,
) -> APIEnvelope[PolicyRuleOut]:
    assert current_user is not None
    return APIEnvelope(data=create_policy_rule(db, payload))


@api.patch("/policies/{policy_id}", response_model=APIEnvelope[PolicyRuleOut])
def patch_policy(
    policy_id: int,
    payload: PolicyRuleUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(require_roles("finance_admin"))] = None,
) -> APIEnvelope[PolicyRuleOut]:
    assert current_user is not None
    return APIEnvelope(data=patch_policy_rule(db, policy_id, payload))


@api.get("/budgets", response_model=APIEnvelope[list[dict]])
def budgets(
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(get_current_user)] = None,
) -> APIEnvelope[list[dict]]:
    assert current_user is not None
    return APIEnvelope(data=get_budget_overview(db, current_user))


@api.get("/anomalies", response_model=APIEnvelope[list[dict]])
def anomalies(
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(require_roles("manager", "finance_admin"))] = None,
) -> APIEnvelope[list[dict]]:
    assert current_user is not None
    return APIEnvelope(data=get_flagged_claims(db, current_user))


@api.get("/audit", response_model=APIEnvelope[list[dict]])
def audit(
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(require_roles("finance_admin", "manager"))] = None,
) -> APIEnvelope[list[dict]]:
    assert current_user is not None
    return APIEnvelope(data=get_audit_trail())


@api.get("/departments", response_model=APIEnvelope[list[dict]])
def departments(
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(get_current_user)] = None,
) -> APIEnvelope[list[dict]]:
    assert current_user is not None
    return APIEnvelope(data=get_department_directory())


@api.get("/finance/summary", response_model=APIEnvelope[FinanceSummaryOut])
def finance_summary(
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(require_roles("finance_admin"))] = None,
) -> APIEnvelope[FinanceSummaryOut]:
    assert current_user is not None
    return APIEnvelope(data=get_finance_summary(db))


@api.post("/chat", response_model=APIEnvelope[ChatResponse])
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Annotated[UserOut, Depends(get_current_user)] = None,
) -> APIEnvelope[ChatResponse]:
    assert current_user is not None
    return APIEnvelope(data=get_spend_chat_response(db, current_user, payload))


router.include_router(api)

