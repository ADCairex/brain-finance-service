from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user_id
from ..models import Account
from ..schemas import AccountCreate, AccountOut, AccountUpdate

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountOut])
def list_accounts(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return db.query(Account).filter(Account.user_id == user_id).all()


@router.post("", response_model=AccountOut, status_code=201)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account = Account(**data.model_dump(), user_id=user_id)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountOut)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("/{account_id}", response_model=AccountOut)
def update_account(
    account_id: int,
    data: AccountUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    for key, value in data.model_dump().items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=204)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    db.delete(account)
    db.commit()
