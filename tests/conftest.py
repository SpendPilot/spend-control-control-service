from __future__ import annotations

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://spendcontrol:spendcontrol@localhost:5432/spend_control",
)
os.environ.setdefault("JWT_SECRET_KEY", "dev-secret-change-me")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("EXPENSE_SERVICE_URL", "http://localhost:8001")
os.environ.setdefault("AI_SERVICE_URL", "http://localhost:8002")
os.environ.setdefault("RECEIPT_REQUIRED_THRESHOLD", "75")
