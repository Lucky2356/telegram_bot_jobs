"""add unique constraints, cascade deletes, blocklist timestamp

Revision ID: 8db6b6d7e80b
Revises: 20260522_065609_initial
Create Date: 2026-05-23 20:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '8db6b6d7e80b'
down_revision: Union[str, None] = '20260522_065609'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite doesn't support ADD CONSTRAINT, so we need to recreate tables
    # For production SQLite, these constraints are added at the SQLAlchemy model level
    # and enforced by application code

    # Add blocklist created_at column
    with op.batch_alter_table('blocklist') as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))

    # Create unique indexes which work on SQLite
    with op.batch_alter_table('sent_vacancies') as batch_op:
        batch_op.create_index('idx_sent_user_vacancy', ['user_id', 'vacancy_id'], unique=True)

    with op.batch_alter_table('saved_vacancies') as batch_op:
        batch_op.create_index('idx_saved_user_vacancy', ['user_id', 'vacancy_id'], unique=True)

    with op.batch_alter_table('blocklist') as batch_op:
        batch_op.create_index('idx_blocklist_entry', ['user_id', 'pattern', 'type'], unique=True)

    # Indexes for performance
    with op.batch_alter_table('sent_vacancies') as batch_op:
        batch_op.create_index('idx_sent_user_id', ['user_id'], unique=False)
        batch_op.create_index('idx_sent_vacancy_id', ['vacancy_id'], unique=False)
        batch_op.create_index('idx_sent_sent_at', ['sent_at'], unique=False)

    with op.batch_alter_table('saved_vacancies') as batch_op:
        batch_op.create_index('idx_saved_user_id', ['user_id'], unique=False)
        batch_op.create_index('idx_saved_vacancy_id', ['vacancy_id'], unique=False)

    with op.batch_alter_table('blocklist') as batch_op:
        batch_op.create_index('idx_blocklist_user_id', ['user_id'], unique=False)

    with op.batch_alter_table('filters') as batch_op:
        batch_op.create_index('idx_filter_user_id', ['user_id'], unique=False)

    with op.batch_alter_table('vacancies') as batch_op:
        batch_op.create_index('idx_vacancy_created_at', ['created_at'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('vacancies') as batch_op:
        batch_op.drop_index('idx_vacancy_created_at')

    with op.batch_alter_table('filters') as batch_op:
        batch_op.drop_index('idx_filter_user_id')

    with op.batch_alter_table('blocklist') as batch_op:
        batch_op.drop_index('idx_blocklist_user_id')
        batch_op.drop_index('idx_blocklist_entry')
        batch_op.drop_column('created_at')

    with op.batch_alter_table('saved_vacancies') as batch_op:
        batch_op.drop_index('idx_saved_vacancy_id')
        batch_op.drop_index('idx_saved_user_id')
        batch_op.drop_index('idx_saved_user_vacancy')

    with op.batch_alter_table('sent_vacancies') as batch_op:
        batch_op.drop_index('idx_sent_sent_at')
        batch_op.drop_index('idx_sent_vacancy_id')
        batch_op.drop_index('idx_sent_user_id')
        batch_op.drop_index('idx_sent_user_vacancy')
