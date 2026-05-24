"""initial control schema

Revision ID: 20260524_0001
Revises:
Create Date: 2026-05-24
"""

import sqlalchemy as sa

from alembic import op

revision = "20260524_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS control")

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        schema="control",
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["control.roles.id"]),
        schema="control",
    )

    op.create_table(
        "policy_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rule_type", sa.String(length=100), nullable=False),
        sa.Column("threshold_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="control",
    )

    op.create_table(
        "approval_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("claim_id", sa.Integer(), nullable=False),
        sa.Column("approver_user_id", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["approver_user_id"], ["control.users.id"]),
        schema="control",
    )


def downgrade() -> None:
    for table in ["approval_steps", "policy_rules", "users", "roles"]:
        op.drop_table(table, schema="control")
    op.execute("DROP SCHEMA IF EXISTS control CASCADE")

