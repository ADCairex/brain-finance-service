from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user_id
from ..models import Account, Transfer
from ..schemas import TransferCreate, TransferOut, TransferUpdate

router = APIRouter(prefix="/api/transfers", tags=["transfers"])


def _user_account_ids(db: Session, user_id: int) -> list[int]:
    return [a.id for a in db.query(Account.id).filter(Account.user_id == user_id).all()]


@router.get("", response_model=list[TransferOut])
def list_transfers(
    account_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    query = db.query(Transfer).filter(
        or_(
            Transfer.from_account_id.in_(account_ids),
            Transfer.to_account_id.in_(account_ids),
        )
    )
    if account_id is not None:
        query = query.filter(
            or_(
                Transfer.from_account_id == account_id,
                Transfer.to_account_id == account_id,
            )
        )
    if year:
        query = query.filter(extract("year", Transfer.date) == year)
    if month:
        query = query.filter(extract("month", Transfer.date) == month)

    return query.order_by(Transfer.date.desc()).all()


@router.post("", response_model=TransferOut, status_code=201)
def create_transfer(
    data: TransferCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    transfer = Transfer(**data.model_dump())
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer


@router.get("/{transfer_id}", response_model=TransferOut)
def get_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    transfer = (
        db.query(Transfer)
        .filter(
            Transfer.id == transfer_id,
            or_(
                Transfer.from_account_id.in_(account_ids),
                Transfer.to_account_id.in_(account_ids),
            ),
        )
        .first()
    )
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer


@router.put("/{transfer_id}", response_model=TransferOut)
def update_transfer(
    transfer_id: int,
    data: TransferUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    transfer = (
        db.query(Transfer)
        .filter(
            Transfer.id == transfer_id,
            or_(
                Transfer.from_account_id.in_(account_ids),
                Transfer.to_account_id.in_(account_ids),
            ),
        )
        .first()
    )
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    for key, value in data.model_dump().items():
        setattr(transfer, key, value)
    db.commit()
    db.refresh(transfer)
    return transfer


@router.delete("/{transfer_id}", status_code=204)
def delete_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    transfer = (
        db.query(Transfer)
        .filter(
            Transfer.id == transfer_id,
            or_(
                Transfer.from_account_id.in_(account_ids),
                Transfer.to_account_id.in_(account_ids),
            ),
        )
        .first()
    )
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    db.delete(transfer)
    db.commit()
