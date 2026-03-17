from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user_id
from ..models import Account, Asset
from ..schemas import AssetCreate, AssetOut, AssetUpdate

router = APIRouter(prefix="/api/assets", tags=["assets"])


def _user_account_ids(db: Session, user_id: int) -> list[int]:
    return [a.id for a in db.query(Account.id).filter(Account.user_id == user_id).all()]


@router.get("", response_model=list[AssetOut])
def list_assets(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    return db.query(Asset).filter(Asset.account_id.in_(account_ids)).all()


@router.post("", response_model=AssetOut, status_code=201)
def create_asset(
    data: AssetCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    asset = Asset(**data.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.account_id.in_(account_ids)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.put("/{asset_id}", response_model=AssetOut)
def update_asset(
    asset_id: int,
    data: AssetUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.account_id.in_(account_ids)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    for key, value in data.model_dump().items():
        setattr(asset, key, value)
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=204)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    account_ids = _user_account_ids(db, user_id)
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.account_id.in_(account_ids)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(asset)
    db.commit()
