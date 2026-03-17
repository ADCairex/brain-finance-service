from sqlalchemy import Column, ForeignKey, Integer, String, Numeric, Boolean, Date, Text
from sqlalchemy.orm import relationship

from .database import Base


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

    account = relationship("Account", back_populates="transactions")


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
