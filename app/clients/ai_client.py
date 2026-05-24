from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


class AIServiceClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _url(self, path: str) -> str:
        return f"{self.settings.ai_service_url}{path}"

    def get_weekly_summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(self._url("/api/v1/summaries/weekly"), json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["data"]

    def explain_anomaly(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(self._url("/api/v1/explanations/anomaly"), json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["data"]

    def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(self._url("/api/v1/chat"), json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["data"]

