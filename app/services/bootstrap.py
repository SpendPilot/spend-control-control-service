from __future__ import annotations

import logging
from collections.abc import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import ApprovalStep, PolicyRule, Role, User
from app.services.auth import hash_password

logger = logging.getLogger(__name__)

DEMO_PASSWORD = "Password123!"

ROLE_SEED: tuple[dict[str, object], ...] = (
    {"id": 1, "name": "employee", "description": "Standard employee submitter"},
    {"id": 2, "name": "manager", "description": "Department approver"},
    {"id": 3, "name": "finance_admin", "description": "Finance administrator"},
)

USER_SEED: tuple[dict[str, object], ...] = (
    {
        "id": 1,
        "company_id": 1,
        "department_id": 1,
        "role_id": 1,
        "email": "employee@northstar.test",
        "full_name": "Avery Employee",
    },
    {
        "id": 2,
        "company_id": 1,
        "department_id": 2,
        "role_id": 2,
        "email": "manager@northstar.test",
        "full_name": "Morgan Manager",
    },
    {
        "id": 3,
        "company_id": 1,
        "department_id": 3,
        "role_id": 3,
        "email": "finance@northstar.test",
        "full_name": "Finley Finance",
    },
)


def ensure_control_bootstrap() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS control"))

    Base.metadata.create_all(
        bind=engine,
        tables=[
            Role.__table__,
            User.__table__,
            PolicyRule.__table__,
            ApprovalStep.__table__,
        ],
        checkfirst=True,
    )

    with SessionLocal() as db:
        _ensure_roles(db, ROLE_SEED)
        _ensure_demo_users(db, USER_SEED)
        db.commit()

    logger.info("Control-service bootstrap ensured auth tables and demo users.")


def _ensure_roles(db: Session, roles: Iterable[dict[str, object]]) -> None:
    for payload in roles:
        role = db.query(Role).filter(Role.id == payload["id"]).first()
        if not role:
            db.add(Role(**payload))
            continue
        role.name = str(payload["name"])
        role.description = str(payload["description"])


def _ensure_demo_users(db: Session, users: Iterable[dict[str, object]]) -> None:
    password_hash = hash_password(DEMO_PASSWORD)
    for payload in users:
        user = db.query(User).filter(User.email == payload["email"]).first()
        if not user:
            db.add(
                User(
                    **payload,
                    password_hash=password_hash,
                    is_active=True,
                )
            )
            continue
        user.company_id = int(payload["company_id"])
        user.department_id = int(payload["department_id"])
        user.role_id = int(payload["role_id"])
        user.full_name = str(payload["full_name"])
        user.password_hash = password_hash
        user.is_active = True
