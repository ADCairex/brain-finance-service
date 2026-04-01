import re
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class AccountCreate(BaseModel):
    name: str
    initial_balance: float = 0


class AccountUpdate(BaseModel):
    name: str
    initial_balance: float


class AccountOut(BaseModel):
    id: int
    name: str
    initial_balance: float

    model_config = {"from_attributes": True}


class TransactionBase(BaseModel):
    description: str
    amount: float
    category: str
    date: date
    is_income: bool
    notes: Optional[str] = None
    account_id: Optional[int] = None

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str) and ("T" in v or "Z" in v):
            return datetime.fromisoformat(v.replace("Z", "+00:00")).date()
        return v


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(TransactionBase):
    pass


class TransactionOut(TransactionBase):
    id: int

    model_config = {"from_attributes": True}


class AssetCreate(BaseModel):
    name: str
    value: float
    category: str = "otro"
    acquisition_date: date
    is_initial: bool = False
    account_id: Optional[int] = None
    notes: Optional[str] = None

    @field_validator("acquisition_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str) and ("T" in v or "Z" in v):
            return datetime.fromisoformat(v.replace("Z", "+00:00")).date()
        return v


class AssetUpdate(AssetCreate):
    pass


class AssetOut(BaseModel):
    id: int
    name: str
    value: float
    category: str
    acquisition_date: date
    is_initial: bool
    account_id: Optional[int]
    notes: Optional[str]

    model_config = {"from_attributes": True}


class Summary(BaseModel):
    total_income: float
    total_expenses: float
    total_invested: float
    total_investments_initial: float
    total_assets_acquired: float
    total_transfers_out: float
    total_transfers_in: float
    initial_balance: float
    balance: float
    count: int


class CategoryBreakdown(BaseModel):
    category: str
    total: float


class MonthlyData(BaseModel):
    month: int
    income: float
    expenses: float


class InvestmentInstrumentCreate(BaseModel):
    symbol: str
    name: str
    asset_type: str = "stock"


class InvestmentInstrumentOut(BaseModel):
    symbol: str
    name: str
    asset_type: str

    model_config = {"from_attributes": True}


class InvestmentCreate(BaseModel):
    asset_symbol: str
    asset_name: str  # usado para crear/actualizar el instrumento
    asset_type: str = "stock"
    quantity: float
    purchase_price: float
    purchase_date: date
    source_account_id: Optional[int] = None
    is_initial: bool = False
    notes: Optional[str] = None

    @field_validator("purchase_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str) and ("T" in v or "Z" in v):
            return datetime.fromisoformat(v.replace("Z", "+00:00")).date()
        return v


class InvestmentOut(BaseModel):
    id: int
    asset_symbol: str
    asset_name: str  # viene del instrumento relacionado
    asset_type: str
    quantity: float
    purchase_price: float
    purchase_date: date
    cost_basis: float
    current_price: float
    current_value: float
    profit_loss: float
    profit_loss_pct: float
    source_account_id: Optional[int]
    is_initial: bool
    notes: Optional[str]

    model_config = {"from_attributes": True}


class InvestmentBySymbol(BaseModel):
    asset_symbol: str
    asset_name: str
    total_quantity: float
    avg_purchase_price: float
    cost_basis: float
    current_price: float
    current_value: float
    profit_loss: float
    profit_loss_pct: float
    purchases: list[InvestmentOut]


class InvestmentSummary(BaseModel):
    total_invested: float
    current_value: float
    profit_loss: float
    profit_loss_pct: float


class CategoryCreate(BaseModel):
    name: str
    label: str
    emoji: str
    color: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("El nombre no puede estar vacío")
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("El nombre solo puede contener letras minúsculas, números y guiones")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("El color debe ser un hex válido (ej: #ff5733)")
        return v.lower()

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("La etiqueta no puede estar vacía")
        return v.strip()

    @field_validator("emoji")
    @classmethod
    def validate_emoji(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El emoji no puede estar vacío")
        return v.strip()


class CategoryUpdate(BaseModel):
    label: Optional[str] = None
    emoji: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("El color debe ser un hex válido (ej: #ff5733)")
        return v.lower() if v else v

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("La etiqueta no puede estar vacía")
        return v.strip() if v else v

    @field_validator("emoji")
    @classmethod
    def validate_emoji(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("El emoji no puede estar vacío")
        return v.strip() if v else v


class CategoryOut(BaseModel):
    id: int
    user_id: int
    name: str
    label: str
    emoji: str
    color: str
    is_default: bool
    is_deletable: bool
    sort_order: int

    model_config = {"from_attributes": True}


class TransferCreate(BaseModel):
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    amount: float
    date: date
    description: Optional[str] = None

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str) and ("T" in v or "Z" in v):
            return datetime.fromisoformat(v.replace("Z", "+00:00")).date()
        return v


class TransferUpdate(TransferCreate):
    pass


class TransferOut(BaseModel):
    id: int
    from_account_id: Optional[int]
    to_account_id: Optional[int]
    amount: float
    date: date
    description: Optional[str]

    model_config = {"from_attributes": True}
