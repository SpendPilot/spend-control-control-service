from datetime import datetime

from pydantic import BaseModel


class PolicyRuleCreate(BaseModel):
    name: str
    description: str
    rule_type: str
    threshold_amount: float | None = None
    category: str | None = None
    config_json: dict | None = None
    active: bool = True


class PolicyRuleUpdate(BaseModel):
    description: str | None = None
    threshold_amount: float | None = None
    category: str | None = None
    config_json: dict | None = None
    active: bool | None = None


class PolicyRuleOut(BaseModel):
    id: int
    name: str
    description: str
    rule_type: str
    threshold_amount: float | None = None
    category: str | None = None
    config_json: dict | None = None
    active: bool
    created_at: datetime | None = None

