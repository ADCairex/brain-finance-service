"""add user_id to accounts

Revision ID: 0001
Revises:
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('accounts', sa.Column('user_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('accounts', 'user_id')
