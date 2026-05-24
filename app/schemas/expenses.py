from datetime import date, datetime

from pydantic import BaseModel, Field


class ExpenseItemInput(BaseModel):
    description: str
    amount: float
    category: str
    expense_date: date


class ClaimCreatePublic(BaseModel):
    title: str
    merchant: str
    category: str
    amount: float
    currency: str = "USD"
    expense_date: date
    notes: str | None = None
    items: list[ExpenseItemInput] = Field(default_factory=list)


class ClaimUpdatePublic(BaseModel):
    notes: str | None = None


class ClaimOutPublic(BaseModel):
    id: int
    title: str
    merchant: str
    category: str
    amount: float
    currency: str
    department_id: int
    department_name: str
    expense_date: date
    status: str
    policy_status: str
    reimbursement_state: str
    submitted_by_email: str
    created_at: datetime
    items: list[dict] = Field(default_factory=list)
    receipts: list[dict] = Field(default_factory=list)
    anomalies: list[dict] = Field(default_factory=list)

