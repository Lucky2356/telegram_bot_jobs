"""initial schema

Revision ID: 20260522_065609
Revises:
Create Date: 2026-05-22 06:56:09.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "20260522_065609"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "filters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("keywords", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("employment_types", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("sites", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("exclude_keywords", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("experience", sa.String(10), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "vacancies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("company", sa.String(500), nullable=True),
        sa.Column("salary_text", sa.String(255), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=True),
        sa.Column("experience", sa.String(10), nullable=True),
        sa.Column("city", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("source", "source_id", name="uq_source_vacancy"),
    )
    op.create_table(
        "sent_vacancies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), sa.ForeignKey("vacancies.id"), nullable=False),
        sa.Column("filter_id", sa.Integer(), sa.ForeignKey("filters.id"), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "saved_vacancies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), sa.ForeignKey("vacancies.id"), nullable=False),
        sa.Column("saved_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "blocklist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("pattern", sa.String(500), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("blocklist")
    op.drop_table("saved_vacancies")
    op.drop_table("sent_vacancies")
    op.drop_table("vacancies")
    op.drop_table("filters")
    op.drop_table("users")
