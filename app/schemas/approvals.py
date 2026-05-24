from datetime import datetime

from pydantic import BaseModel


class ApprovalDecision(BaseModel):
    decision: str
    comment: str | None = None


class ApprovalQueueItem(BaseModel):
    claim_id: int
    title: str
    merchant: str
    amount: float
    category: str
    employee_email: str
    submitted_at: datetime
    status: str
    decision: str

