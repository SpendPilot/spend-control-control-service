from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIEnvelope(BaseModel, Generic[T]):
    success: bool = True
    message: str = "ok"
    data: T


class HealthResponse(BaseModel):
    service: str
    status: str = "ok"
    version: str = "0.1.0"
    checks: dict[str, str] = Field(default_factory=dict)

