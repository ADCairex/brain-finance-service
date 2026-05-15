import re
import unicodedata
from datetime import date
from decimal import Decimal
from hashlib import sha256


def normalize_description(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", ascii_value.casefold()).strip()


def normalize_decimal(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01")))


def transaction_fingerprint(
    *,
    provider: str,
    transaction_date: date,
    amount: Decimal,
    description: str,
    account_id: int | None = None,
) -> str:
    parts = [
        provider.casefold().strip(),
        transaction_date.isoformat(),
        normalize_decimal(amount),
        normalize_description(description),
        str(account_id) if account_id is not None else "",
    ]
    return sha256("|".join(parts).encode("utf-8")).hexdigest()
