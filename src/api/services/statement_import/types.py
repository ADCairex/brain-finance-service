from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


class StatementProvider(StrEnum):
    TRADE_REPUBLIC = "trade_republic"


class CandidateClassification(StrEnum):
    IMPORTABLE = "importable"
    EXCLUDED = "excluded"
    DUPLICATE = "duplicate"
    INVALID = "invalid"


@dataclass(frozen=True)
class StatementSummary:
    provider: StatementProvider
    start_date: date | None
    end_date: date | None
    opening_balance: Decimal | None
    total_in: Decimal | None
    total_out: Decimal | None
    closing_balance: Decimal | None


@dataclass(frozen=True)
class ParsedStatementRow:
    source_order: int
    transaction_date: date | None
    raw_type: str
    description: str
    amount: Decimal | None
    balance_after: Decimal | None
    raw_text: str
    provenance: str | None = None


@dataclass(frozen=True)
class ParsedStatement:
    provider: StatementProvider
    summary: StatementSummary
    rows: list[ParsedStatementRow]
    raw_text: str


@dataclass(frozen=True)
class ClassifiedCandidate:
    row: ParsedStatementRow
    classification: CandidateClassification
    is_income: bool | None
    category_hint: str | None
    reason: str | None
    fingerprint: str | None


@dataclass(frozen=True)
class ReconciliationResult:
    opening_balance: Decimal | None
    closing_balance: Decimal | None
    statement_total_in: Decimal
    statement_total_out: Decimal
    parsed_total_in: Decimal
    parsed_total_out: Decimal
    importable_total_in: Decimal
    importable_total_out: Decimal
    excluded_total_in: Decimal
    excluded_total_out: Decimal
    invalid_total_in: Decimal
    invalid_total_out: Decimal
    expected_closing_balance: Decimal | None
    full_statement_matches: bool | None
    importable_net: Decimal
    excluded_net: Decimal
    difference: Decimal | None
