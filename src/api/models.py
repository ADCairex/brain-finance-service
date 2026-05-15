from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_categories_user_id_name"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    label = Column(String(100), nullable=False)
    emoji = Column(String(10), nullable=False)
    color = Column(String(7), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    is_deletable = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    initial_balance = Column(Numeric(12, 2), nullable=False, default=0)
    user_id = Column(Integer, nullable=True, index=True)

    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    category = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    is_income = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    import_fingerprint = Column(String(64), nullable=True, index=True, unique=True)
    source_import_candidate_id = Column(
        Integer,
        ForeignKey("statement_import_candidates.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )

    account = relationship("Account", back_populates="transactions")
    source_import_candidate = relationship("StatementImportCandidate")


class StatementImportSession(Base):
    __tablename__ = "statement_import_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    provider = Column(String(50), nullable=False, index=True)
    source_filename = Column(String(255), nullable=True)
    source_file_hash = Column(String(64), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="parsed")
    statement_start_date = Column(Date, nullable=True)
    statement_end_date = Column(Date, nullable=True)
    opening_balance = Column(Numeric(12, 2), nullable=True)
    closing_balance = Column(Numeric(12, 2), nullable=True)
    statement_total_in = Column(Numeric(12, 2), nullable=True)
    statement_total_out = Column(Numeric(12, 2), nullable=True)
    reconciliation_status = Column(String(50), nullable=True)
    reconciliation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    account = relationship("Account")
    candidates = relationship("StatementImportCandidate", back_populates="session", cascade="all, delete-orphan")


class StatementImportCandidate(Base):
    __tablename__ = "statement_import_candidates"
    __table_args__ = (
        UniqueConstraint("session_id", "source_order", name="uq_statement_import_candidates_session_order"),
    )

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer, ForeignKey("statement_import_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_order = Column(Integer, nullable=False)
    transaction_date = Column(Date, nullable=True, index=True)
    raw_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(12, 2), nullable=True)
    balance_after = Column(Numeric(12, 2), nullable=True)
    classification = Column(String(50), nullable=False)
    category_hint = Column(String(100), nullable=True)
    is_income = Column(Boolean, nullable=True)
    exclusion_reason = Column(String(255), nullable=True)
    validation_error = Column(String(255), nullable=True)
    fingerprint = Column(String(64), nullable=True, index=True)
    duplicate_transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    raw_text = Column(Text, nullable=False)
    provenance = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    session = relationship("StatementImportSession", back_populates="candidates")
    duplicate_transaction = relationship("Transaction", foreign_keys=[duplicate_transaction_id])


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    value = Column(Numeric(12, 2), nullable=False)
    category = Column(String(100), nullable=False, default="otro")
    acquisition_date = Column(Date, nullable=False)
    is_initial = Column(Boolean, nullable=False, default=False)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)

    account = relationship("Account")


class InvestmentInstrument(Base):
    __tablename__ = "investment_instruments"

    symbol = Column(String(20), primary_key=True)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(50), nullable=False, default="stock")  # stock, etf, crypto, fund

    purchases = relationship("Investment", back_populates="instrument")


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    asset_symbol = Column(String(20), ForeignKey("investment_instruments.symbol"), nullable=False)
    quantity = Column(Numeric(18, 8), nullable=False)
    purchase_price = Column(Numeric(12, 2), nullable=False)
    purchase_date = Column(Date, nullable=False)
    source_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    is_initial = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)

    instrument = relationship("InvestmentInstrument", back_populates="purchases")
    source_account = relationship("Account")


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)
    from_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String(255), nullable=True)

    from_account = relationship("Account", foreign_keys=[from_account_id])
    to_account = relationship("Account", foreign_keys=[to_account_id])
