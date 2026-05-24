from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "control"}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str] = mapped_column(String(255))


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "control"}

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column()
    department_id: Mapped[int | None] = mapped_column(nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("control.roles.id"))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    role: Mapped[Role] = relationship(lazy="joined")


class PolicyRule(Base):
    __tablename__ = "policy_rules"
    __table_args__ = {"schema": "control"}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text())
    rule_type: Mapped[str] = mapped_column(String(100))
    threshold_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean(), default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ApprovalStep(Base):
    __tablename__ = "approval_steps"
    __table_args__ = {"schema": "control"}

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column()
    approver_user_id: Mapped[int] = mapped_column(ForeignKey("control.users.id"))
    decision: Mapped[str] = mapped_column(String(50), default="pending")
    comment: Mapped[str | None] = mapped_column(Text(), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    approver: Mapped[User] = relationship(lazy="joined")

