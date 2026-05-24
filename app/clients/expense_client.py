from __future__ import annotations

from typing import Any

import httpx
from fastapi import UploadFile

from app.core.config import get_settings


class ExpenseServiceClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _url(self, path: str) -> str:
        return f"{self.settings.expense_service_url}{path}"

    def list_claims(self, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        response = httpx.get(self._url("/api/v1/claims"), params=params, timeout=30)
        response.raise_for_status()
        return response.json()["data"]

    def create_claim(self, payload: dict[str, Any], actor_email: str) -> dict[str, Any]:
        response = httpx.post(
            self._url("/api/v1/claims"),
            json=payload,
            headers={"X-Actor-Email": actor_email},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["data"]

    def get_claim(self, claim_id: int) -> dict[str, Any]:
        response = httpx.get(self._url(f"/api/v1/claims/{claim_id}"), timeout=30)
        response.raise_for_status()
        return response.json()["data"]

    def patch_claim(self, claim_id: int, payload: dict[str, Any], actor_email: str) -> dict[str, Any]:
        response = httpx.patch(
            self._url(f"/api/v1/claims/{claim_id}"),
            json=payload,
            headers={"X-Actor-Email": actor_email},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["data"]

    async def upload_receipt(
        self,
        claim_id: int,
        file: UploadFile,
        actor_email: str,
        corrected_merchant: str | None,
        corrected_amount: float | None,
        corrected_date: str | None,
    ) -> dict[str, Any]:
        content = await file.read()
        files = {"file": (file.filename or "receipt.bin", content, file.content_type or "application/octet-stream")}
        data = {
            "corrected_merchant": corrected_merchant or "",
            "corrected_amount": corrected_amount or "",
            "corrected_date": corrected_date or "",
        }
        response = httpx.post(
            self._url(f"/api/v1/claims/{claim_id}/receipts"),
            files=files,
            data=data,
            headers={"X-Actor-Email": actor_email},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["data"]

    def get_departments(self) -> list[dict[str, Any]]:
        response = httpx.get(self._url("/api/v1/departments"), timeout=30)
        response.raise_for_status()
        return response.json()["data"]

    def get_budgets(self) -> list[dict[str, Any]]:
        response = httpx.get(self._url("/api/v1/budgets"), timeout=30)
        response.raise_for_status()
        return response.json()["data"]

    def get_anomalies(self) -> list[dict[str, Any]]:
        response = httpx.get(self._url("/api/v1/anomalies"), timeout=30)
        response.raise_for_status()
        return response.json()["data"]

    def get_audit_events(self) -> list[dict[str, Any]]:
        response = httpx.get(self._url("/api/v1/audit-events"), timeout=30)
        response.raise_for_status()
        return response.json()["data"]

    def get_analytics(self) -> dict[str, Any]:
        response = httpx.get(self._url("/api/v1/analytics/overview"), timeout=30)
        response.raise_for_status()
        return response.json()["data"]

