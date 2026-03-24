from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user_id
from ..models import Account, Asset, Investment, Transaction
from ..schemas import (
    CategoryBreakdown,
    MonthlyData,
    Summary,
    TransactionCreate,
    TransactionOut,
    TransactionUpdate,
)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _user_account_ids(db: Session, user_id: int) -> list[int]:
    return [a.id for a in db.query(Account.id).filter(Account.user_id == user_id).all()]


# Static routes must come before /{id} to avoid route conflicts
@router.get("/summary", response_model=Summary)
def get_summary(
    month: Optional[int] = None,
    year: Optional[int] = None,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)

    query = db.query(Transaction).filter(Transaction.account_id.in_(account_ids))
    if month:
        query = query.filter(extract("month", Transaction.date) == month)
    if year:
        query = query.filter(extract("year", Transaction.date) == year)
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    transactions = query.all()
    total_income = sum(float(t.amount) for t in transactions if t.is_income)
    total_expenses = sum(float(t.amount) for t in transactions if not t.is_income)

    if account_id is not None:
        account = db.query(Account).filter(Account.id == account_id, Account.user_id == user_id).first()
        initial_balance = float(account.initial_balance) if account else 0.0
        inv_query = db.query(Investment).filter(Investment.source_account_id == account_id)
        asset_query = db.query(Asset).filter(Asset.account_id == account_id)
    else:
        initial_balance = sum(
            float(a.initial_balance) for a in db.query(Account).filter(Account.user_id == user_id).all()
        )
        inv_query = db.query(Investment).filter(Investment.source_account_id.in_(account_ids))
        asset_query = db.query(Asset).filter(Asset.account_id.in_(account_ids))

    all_investments = inv_query.all()
    total_invested = sum(float(i.quantity) * float(i.purchase_price) for i in all_investments if not i.is_initial)
    total_investments_initial = sum(
        float(i.quantity) * float(i.purchase_price) for i in all_investments if i.is_initial
    )

    all_assets = asset_query.all()
    total_assets_initial = sum(float(a.value) for a in all_assets if a.is_initial)
    total_assets_acquired = sum(float(a.value) for a in all_assets if not a.is_initial)

    balance = (
        initial_balance + total_assets_initial + total_income - total_expenses - total_invested - total_assets_acquired
    )

    return Summary(
        total_income=total_income,
        total_expenses=total_expenses,
        total_invested=total_invested,
        total_investments_initial=total_investments_initial,
        total_assets_initial=total_assets_initial,
        total_assets_acquired=total_assets_acquired,
        initial_balance=initial_balance,
        balance=balance,
        balance_with_investments=balance + total_investments_initial,
        count=len(transactions),
    )


@router.get("/by-category", response_model=list[CategoryBreakdown])
def get_by_category(
    month: Optional[int] = None,
    year: Optional[int] = None,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    query = db.query(Transaction).filter(
        Transaction.is_income.is_(False),
        Transaction.account_id.in_(account_ids),
    )
    if month:
        query = query.filter(extract("month", Transaction.date) == month)
    if year:
        query = query.filter(extract("year", Transaction.date) == year)
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    totals: dict[str, float] = {}
    for t in query.all():
        totals[t.category] = totals.get(t.category, 0.0) + float(t.amount)

    return [CategoryBreakdown(category=k, total=v) for k, v in totals.items()]


@router.get("/by-month", response_model=list[MonthlyData])
def get_by_month(
    year: Optional[int] = None,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    target_year = year or datetime.now().year
    query = db.query(Transaction).filter(
        extract("year", Transaction.date) == target_year,
        Transaction.account_id.in_(account_ids),
    )
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    monthly: dict[int, dict[str, float]] = {i: {"income": 0.0, "expenses": 0.0} for i in range(1, 13)}
    for t in query.all():
        month_num = t.date.month
        if t.is_income:
            monthly[month_num]["income"] += float(t.amount)
        else:
            monthly[month_num]["expenses"] += float(t.amount)

    return [
        MonthlyData(
            month=i,
            income=monthly[i]["income"],
            expenses=monthly[i]["expenses"],
        )
        for i in range(1, 13)
    ]


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    month: Optional[int] = None,
    year: Optional[int] = None,
    category: Optional[str] = None,
    is_income: Optional[bool] = None,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    query = db.query(Transaction).filter(Transaction.account_id.in_(account_ids))
    if month:
        query = query.filter(extract("month", Transaction.date) == month)
    if year:
        query = query.filter(extract("year", Transaction.date) == year)
    if category:
        query = query.filter(Transaction.category == category)
    if is_income is not None:
        query = query.filter(Transaction.is_income.is_(is_income))
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    return query.order_by(Transaction.date.desc()).all()


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    t = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.account_id.in_(account_ids),
        )
        .first()
    )
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return t


@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    t = Transaction(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.put("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    t = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.account_id.in_(account_ids),
        )
        .first()
    )
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for key, value in data.model_dump().items():
        setattr(t, key, value)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    t = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.account_id.in_(account_ids),
        )
        .first()
    )
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(t)
    db.commit()
