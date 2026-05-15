"""add statement import foundation

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-15 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "statement_import_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=True),
        sa.Column("source_file_hash", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("statement_start_date", sa.Date(), nullable=True),
        sa.Column("statement_end_date", sa.Date(), nullable=True),
        sa.Column("opening_balance", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("closing_balance", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("statement_total_in", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("statement_total_out", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("reconciliation_status", sa.String(length=50), nullable=True),
        sa.Column("reconciliation_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_statement_import_sessions_account_id"), "statement_import_sessions", ["account_id"])
    op.create_index(op.f("ix_statement_import_sessions_id"), "statement_import_sessions", ["id"])
    op.create_index(op.f("ix_statement_import_sessions_provider"), "statement_import_sessions", ["provider"])
    op.create_index(
        op.f("ix_statement_import_sessions_source_file_hash"),
        "statement_import_sessions",
        ["source_file_hash"],
    )
    op.create_index(op.f("ix_statement_import_sessions_user_id"), "statement_import_sessions", ["user_id"])

    op.create_table(
        "statement_import_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("source_order", sa.Integer(), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=True),
        sa.Column("raw_type", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("balance_after", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("classification", sa.String(length=50), nullable=False),
        sa.Column("category_hint", sa.String(length=100), nullable=True),
        sa.Column("is_income", sa.Boolean(), nullable=True),
        sa.Column("exclusion_reason", sa.String(length=255), nullable=True),
        sa.Column("validation_error", sa.String(length=255), nullable=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=True),
        sa.Column("duplicate_transaction_id", sa.Integer(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["duplicate_transaction_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["statement_import_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "source_order", name="uq_statement_import_candidates_session_order"),
    )
    op.create_index(op.f("ix_statement_import_candidates_fingerprint"), "statement_import_candidates", ["fingerprint"])
    op.create_index(op.f("ix_statement_import_candidates_id"), "statement_import_candidates", ["id"])
    op.create_index(op.f("ix_statement_import_candidates_session_id"), "statement_import_candidates", ["session_id"])
    op.create_index(
        op.f("ix_statement_import_candidates_transaction_date"),
        "statement_import_candidates",
        ["transaction_date"],
    )

    op.add_column("transactions", sa.Column("import_fingerprint", sa.String(length=64), nullable=True))
    op.add_column("transactions", sa.Column("source_import_candidate_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_transactions_import_fingerprint"), "transactions", ["import_fingerprint"], unique=True)
    op.create_foreign_key(
        "fk_transactions_source_import_candidate_id_statement_import_candidates",
        "transactions",
        "statement_import_candidates",
        ["source_import_candidate_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_transactions_source_import_candidate_id_statement_import_candidates",
        "transactions",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_transactions_import_fingerprint"), table_name="transactions")
    op.drop_column("transactions", "source_import_candidate_id")
    op.drop_column("transactions", "import_fingerprint")

    op.drop_index(op.f("ix_statement_import_candidates_transaction_date"), table_name="statement_import_candidates")
    op.drop_index(op.f("ix_statement_import_candidates_session_id"), table_name="statement_import_candidates")
    op.drop_index(op.f("ix_statement_import_candidates_id"), table_name="statement_import_candidates")
    op.drop_index(op.f("ix_statement_import_candidates_fingerprint"), table_name="statement_import_candidates")
    op.drop_table("statement_import_candidates")

    op.drop_index(op.f("ix_statement_import_sessions_user_id"), table_name="statement_import_sessions")
    op.drop_index(op.f("ix_statement_import_sessions_source_file_hash"), table_name="statement_import_sessions")
    op.drop_index(op.f("ix_statement_import_sessions_provider"), table_name="statement_import_sessions")
    op.drop_index(op.f("ix_statement_import_sessions_id"), table_name="statement_import_sessions")
    op.drop_index(op.f("ix_statement_import_sessions_account_id"), table_name="statement_import_sessions")
    op.drop_table("statement_import_sessions")
