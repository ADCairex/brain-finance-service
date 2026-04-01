from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user_id
from ..models import Account, Category, Transaction
from ..schemas import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["categories"])

DEFAULT_CATEGORIES = [
    {"name": "comida", "label": "Comida", "emoji": "🍔", "color": "#f97316", "sort_order": 1},
    {"name": "transporte", "label": "Transporte", "emoji": "🚗", "color": "#3b82f6", "sort_order": 2},
    {"name": "entretenimiento", "label": "Entretenimiento", "emoji": "🎬", "color": "#a855f7", "sort_order": 3},
    {"name": "salud", "label": "Salud", "emoji": "💊", "color": "#22c55e", "sort_order": 4},
    {"name": "compras", "label": "Compras", "emoji": "🛍️", "color": "#ec4899", "sort_order": 5},
    {"name": "servicios", "label": "Servicios", "emoji": "📱", "color": "#06b6d4", "sort_order": 6},
    {"name": "educacion", "label": "Educación", "emoji": "📚", "color": "#eab308", "sort_order": 7},
    {"name": "casa", "label": "Casa", "emoji": "🏠", "color": "#8b5cf6", "sort_order": 8},
    {"name": "otros", "label": "Otros", "emoji": "📦", "color": "#64748b", "sort_order": 9, "is_deletable": False},
]


def _seed_defaults(db: Session, user_id: int) -> None:
    """Insert default categories for a user. Skips existing ones."""
    for cat in DEFAULT_CATEGORIES:
        exists = db.query(Category.id).filter(Category.user_id == user_id, Category.name == cat["name"]).first()
        if not exists:
            db.add(Category(user_id=user_id, is_default=True, **cat))
    db.commit()


@router.get("/", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    categories = db.query(Category).filter(Category.user_id == user_id).order_by(Category.sort_order).all()
    if not categories:
        _seed_defaults(db, user_id)
        categories = db.query(Category).filter(Category.user_id == user_id).order_by(Category.sort_order).all()
    return categories


@router.post("/", response_model=CategoryOut, status_code=201)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    # Ensure user has defaults seeded
    existing = db.query(Category).filter(Category.user_id == user_id).count()
    if existing == 0:
        _seed_defaults(db, user_id)

    max_order = (
        db.query(Category.sort_order).filter(Category.user_id == user_id).order_by(Category.sort_order.desc()).first()
    )
    next_order = (max_order[0] + 1) if max_order else 1

    category = Category(
        user_id=user_id,
        name=data.name,
        label=data.label,
        emoji=data.emoji,
        color=data.color,
        is_default=False,
        is_deletable=True,
        sort_order=next_order,
    )
    try:
        db.add(category)
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una categoría con ese nombre")
    return category


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if not category.is_deletable:
        raise HTTPException(status_code=400, detail="Esta categoría no se puede eliminar")

    # Reassign transactions to "otros"
    account_ids = [a.id for a in db.query(Account.id).filter(Account.user_id == user_id).all()]
    if account_ids:
        db.query(Transaction).filter(
            Transaction.category == category.name,
            Transaction.account_id.in_(account_ids),
        ).update({Transaction.category: "otros"}, synchronize_session="fetch")

    db.delete(category)
    db.commit()
