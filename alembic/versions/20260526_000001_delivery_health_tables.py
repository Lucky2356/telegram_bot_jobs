"""add telegram delivery and parser health tables

Revision ID: 20260526_000001
Revises: 8db6b6d7e80b
Create Date: 2026-05-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260526_000001"
down_revision: str | Sequence[str] | None = "8db6b6d7e80b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "telegram_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_telegram_deliveries_status", "telegram_deliveries", ["status"])
    op.create_index("ix_telegram_deliveries_updated_at", "telegram_deliveries", ["updated_at"])

    op.create_table(
        "parser_health",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site", sa.String(length=50), nullable=False),
        sa.Column("ok", sa.Boolean(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("site"),
    )
    op.create_index("ix_vacancies_created_at", "vacancies", ["created_at"])
    op.create_index("ix_vacancies_title", "vacancies", ["title"])
    op.create_index("ix_sent_vacancies_sent_at", "sent_vacancies", ["sent_at"])
    op.create_index("ix_filters_user_id", "filters", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_filters_user_id", table_name="filters")
    op.drop_index("ix_sent_vacancies_sent_at", table_name="sent_vacancies")
    op.drop_index("ix_vacancies_title", table_name="vacancies")
    op.drop_index("ix_vacancies_created_at", table_name="vacancies")
    op.drop_table("parser_health")
    op.drop_index("ix_telegram_deliveries_updated_at", table_name="telegram_deliveries")
    op.drop_index("ix_telegram_deliveries_status", table_name="telegram_deliveries")
    op.drop_table("telegram_deliveries")
