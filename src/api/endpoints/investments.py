from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import yfinance as yf

from ..database import get_db
from ..dependencies import get_current_user_id
from ..models import Account, Investment, InvestmentInstrument
from ..schemas import (
    InvestmentBySymbol,
    InvestmentCreate,
    InvestmentInstrumentCreate,
    InvestmentInstrumentOut,
    InvestmentOut,
    InvestmentSummary,
)

router = APIRouter(prefix="/api/investments", tags=["investments"])


def _user_account_ids(db: Session, user_id: int) -> list[int]:
    return [a.id for a in db.query(Account.id).filter(Account.user_id == user_id).all()]


def _fetch_current_price(symbol: str) -> float:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        return float(info.last_price)
    except Exception:
        return 0.0


def _enrich(inv: Investment, current_price: float | None = None) -> InvestmentOut:
    quantity = float(inv.quantity)
    purchase_price = float(inv.purchase_price)
    cost_basis = quantity * purchase_price
    if current_price is None:
        current_price = _fetch_current_price(inv.asset_symbol)
    current_value = quantity * current_price
    profit_loss = current_value - cost_basis
    profit_loss_pct = (profit_loss / cost_basis * 100) if cost_basis else 0.0

    return InvestmentOut(
        id=inv.id,
        asset_symbol=inv.asset_symbol,
        asset_name=inv.instrument.name,
        asset_type=inv.instrument.asset_type,
        quantity=quantity,
        purchase_price=purchase_price,
        purchase_date=inv.purchase_date,
        cost_basis=cost_basis,
        current_price=current_price,
        current_value=current_value,
        profit_loss=profit_loss,
        profit_loss_pct=round(profit_loss_pct, 2),
        source_account_id=inv.source_account_id,
        is_initial=inv.is_initial,
        notes=inv.notes,
    )


def _fetch_prices_for(investments: list[Investment]) -> dict[str, float]:
    symbols = {inv.asset_symbol for inv in investments}
    return {s: _fetch_current_price(s) for s in symbols}


def _upsert_instrument(db: Session, symbol: str, name: str, asset_type: str) -> InvestmentInstrument:
    instrument = db.query(InvestmentInstrument).filter(InvestmentInstrument.symbol == symbol).first()
    if instrument:
        instrument.name = name
        instrument.asset_type = asset_type
    else:
        instrument = InvestmentInstrument(symbol=symbol, name=name, asset_type=asset_type)
        db.add(instrument)
    return instrument


# --- Instruments ---

@router.get("/instruments", response_model=list[InvestmentInstrumentOut])
def list_instruments(db: Session = Depends(get_db)):
    return db.query(InvestmentInstrument).order_by(InvestmentInstrument.symbol).all()


@router.post("/instruments", response_model=InvestmentInstrumentOut, status_code=201)
def create_instrument(data: InvestmentInstrumentCreate, db: Session = Depends(get_db)):
    instrument = _upsert_instrument(db, data.symbol.upper(), data.name, data.asset_type)
    db.commit()
    db.refresh(instrument)
    return instrument


# --- Investments ---

@router.get("/summary", response_model=InvestmentSummary)
def get_investment_summary(
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    query = db.query(Investment).filter(Investment.source_account_id.in_(account_ids))
    if account_id is not None:
        query = query.filter(Investment.source_account_id == account_id)
    investments = query.all()
    prices = _fetch_prices_for(investments)
    enriched = [_enrich(inv, prices[inv.asset_symbol]) for inv in investments]

    total_invested = sum(e.cost_basis for e in enriched)
    current_value = sum(e.current_value for e in enriched)
    profit_loss = current_value - total_invested
    profit_loss_pct = (profit_loss / total_invested * 100) if total_invested else 0.0

    return InvestmentSummary(
        total_invested=total_invested,
        current_value=current_value,
        profit_loss=profit_loss,
        profit_loss_pct=round(profit_loss_pct, 2),
    )


@router.get("/by-symbol", response_model=list[InvestmentBySymbol])
def list_by_symbol(
    is_initial: Optional[bool] = None,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    query = db.query(Investment).filter(Investment.source_account_id.in_(account_ids))
    if is_initial is not None:
        query = query.filter(Investment.is_initial.is_(is_initial))
    if account_id is not None:
        query = query.filter(Investment.source_account_id == account_id)
    investments = query.order_by(Investment.purchase_date).all()

    groups: dict[str, list[Investment]] = {}
    for inv in investments:
        groups.setdefault(inv.asset_symbol, []).append(inv)

    result = []
    for symbol, invs in groups.items():
        current_price = _fetch_current_price(symbol)

        purchases = []
        for inv in invs:
            quantity = float(inv.quantity)
            purchase_price = float(inv.purchase_price)
            cost_basis = quantity * purchase_price
            current_value = quantity * current_price
            profit_loss = current_value - cost_basis
            profit_loss_pct = (profit_loss / cost_basis * 100) if cost_basis else 0.0
            purchases.append(InvestmentOut(
                id=inv.id,
                asset_symbol=inv.asset_symbol,
                asset_name=inv.instrument.name,
                asset_type=inv.instrument.asset_type,
                quantity=quantity,
                purchase_price=purchase_price,
                purchase_date=inv.purchase_date,
                cost_basis=cost_basis,
                current_price=current_price,
                current_value=current_value,
                profit_loss=profit_loss,
                profit_loss_pct=round(profit_loss_pct, 2),
                source_account_id=inv.source_account_id,
                is_initial=inv.is_initial,
                notes=inv.notes,
            ))

        total_quantity = sum(p.quantity for p in purchases)
        total_cost = sum(p.cost_basis for p in purchases)
        avg_price = total_cost / total_quantity if total_quantity else 0.0
        total_current_value = sum(p.current_value for p in purchases)
        total_pl = total_current_value - total_cost
        total_pl_pct = (total_pl / total_cost * 100) if total_cost else 0.0

        result.append(InvestmentBySymbol(
            asset_symbol=symbol,
            asset_name=invs[0].instrument.name,
            total_quantity=total_quantity,
            avg_purchase_price=round(avg_price, 2),
            cost_basis=total_cost,
            current_price=current_price,
            current_value=total_current_value,
            profit_loss=total_pl,
            profit_loss_pct=round(total_pl_pct, 2),
            purchases=purchases,
        ))

    return result


@router.get("", response_model=list[InvestmentOut])
def list_investments(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    investments = db.query(Investment).filter(Investment.source_account_id.in_(account_ids)).all()
    prices = _fetch_prices_for(investments)
    return [_enrich(inv, prices[inv.asset_symbol]) for inv in investments]


@router.post("", response_model=InvestmentOut, status_code=201)
def create_investment(
    data: InvestmentCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    symbol = data.asset_symbol.upper()
    _upsert_instrument(db, symbol, data.asset_name, data.asset_type)
    db.flush()

    inv = Investment(
        asset_symbol=symbol,
        quantity=data.quantity,
        purchase_price=data.purchase_price,
        purchase_date=data.purchase_date,
        source_account_id=data.source_account_id,
        is_initial=data.is_initial,
        notes=data.notes,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return _enrich(inv)


@router.delete("/{investment_id}", status_code=204)
def delete_investment(
    investment_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    inv = db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.source_account_id.in_(account_ids),
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
    db.delete(inv)
    db.commit()
