from collections.abc import Iterable

from .fingerprint import transaction_fingerprint
from .types import CandidateClassification, ClassifiedCandidate, ParsedStatementRow, StatementProvider

INVESTMENT_TERMS = (
    "operar",
    "savings plan execution",
    "buy trade",
    "sell trade",
    "orden de compra",
    "quantity:",
    "ucits etf",
)
TRANSFER_TERMS = (
    "transferencia",
    "incoming transfer",
    "outgoing transfer",
)


def classify_rows(
    rows: Iterable[ParsedStatementRow],
    *,
    provider: StatementProvider = StatementProvider.TRADE_REPUBLIC,
    account_id: int | None = None,
    existing_fingerprints: set[str] | None = None,
) -> list[ClassifiedCandidate]:
    seen = set(existing_fingerprints or set())
    classified: list[ClassifiedCandidate] = []
    for row in rows:
        candidate = classify_row(row, provider=provider, account_id=account_id, existing_fingerprints=seen)
        classified.append(candidate)
        if candidate.fingerprint:
            seen.add(candidate.fingerprint)
    return classified


def classify_row(
    row: ParsedStatementRow,
    *,
    provider: StatementProvider = StatementProvider.TRADE_REPUBLIC,
    account_id: int | None = None,
    existing_fingerprints: set[str] | None = None,
) -> ClassifiedCandidate:
    validation_error = _validation_error(row)
    if validation_error:
        return ClassifiedCandidate(row, CandidateClassification.INVALID, None, None, validation_error, None)

    assert row.transaction_date is not None
    assert row.amount is not None
    fingerprint = transaction_fingerprint(
        provider=provider.value,
        transaction_date=row.transaction_date,
        amount=row.amount,
        description=row.description,
        account_id=account_id,
    )
    if existing_fingerprints and fingerprint in existing_fingerprints:
        return ClassifiedCandidate(
            row, CandidateClassification.DUPLICATE, None, None, "Duplicate transaction fingerprint", fingerprint
        )

    searchable_text = f"{row.raw_type} {row.description} {row.raw_text}".casefold()
    if any(term in searchable_text for term in INVESTMENT_TERMS):
        return ClassifiedCandidate(
            row, CandidateClassification.EXCLUDED, _is_income(row), None, "Investment/trading operation", fingerprint
        )
    if any(term in searchable_text for term in TRANSFER_TERMS):
        return ClassifiedCandidate(
            row, CandidateClassification.EXCLUDED, _is_income(row), None, "Internal or suspected transfer", fingerprint
        )

    is_income = _is_income(row)
    return ClassifiedCandidate(
        row, CandidateClassification.IMPORTABLE, is_income, _category_hint(row, is_income), None, fingerprint
    )


def _validation_error(row: ParsedStatementRow) -> str | None:
    if row.transaction_date is None:
        return "Missing transaction date"
    if row.amount is None:
        return "Missing transaction amount"
    if not row.description.strip():
        return "Missing transaction description"
    return None


def _is_income(row: ParsedStatementRow) -> bool:
    text = f"{row.raw_type} {row.description}".casefold()
    return (
        "interés" in text
        or "interest" in text
        or "bonificación" in text
        or "bonus" in text
        or "incoming transfer" in text
    )


def _category_hint(row: ParsedStatementRow, is_income: bool) -> str:
    if is_income:
        return "ingreso"
    if "Transacción" in row.raw_type or "con tarjeta" in row.raw_text:
        return "compras"
    return "otros"
