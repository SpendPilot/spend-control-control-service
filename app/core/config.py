from functools import lru_cache

from pydantic import Field

from spend_control_shared.settings import CommonSettings


class Settings(CommonSettings):
    expense_service_url: str = Field(default="http://localhost:8001", alias="EXPENSE_SERVICE_URL")
    ai_service_url: str = Field(default="http://localhost:8002", alias="AI_SERVICE_URL")
    receipt_required_threshold: float = Field(default=75.0, alias="RECEIPT_REQUIRED_THRESHOLD")


@lru_cache
def get_settings() -> Settings:
    return Settings()

