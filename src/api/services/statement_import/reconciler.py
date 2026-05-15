from decimal import Decimal

from .types import CandidateClassification, ClassifiedCandidate, ParsedStatement, ReconciliationResult

ZERO = Decimal("0.00")


def reconcile_statement(statement: ParsedStatement, candidates: list[ClassifiedCandidate]) -> ReconciliationResult:
    parsed_total_in, parsed_total_out = _totals(
        candidates, CandidateClassification.IMPORTABLE, CandidateClassification.EXCLUDED
    )
    importable_total_in, importable_total_out = _totals(candidates, CandidateClassification.IMPORTABLE)
    excluded_total_in, excluded_total_out = _totals(candidates, CandidateClassification.EXCLUDED)
    invalid_total_in, invalid_total_out = _totals(candidates, CandidateClassification.INVALID)
    summary = statement.summary
    expected_closing = None
    full_matches = None
    difference = None
    if summary.opening_balance is not None and summary.closing_balance is not None:
        expected_closing = (summary.opening_balance + parsed_total_in - parsed_total_out).quantize(Decimal("0.01"))
        difference = (summary.closing_balance - expected_closing).quantize(Decimal("0.01"))
        full_matches = difference == ZERO
    return ReconciliationResult(
        opening_balance=summary.opening_balance,
        closing_balance=summary.closing_balance,
        statement_total_in=summary.total_in or ZERO,
        statement_total_out=summary.total_out or ZERO,
        parsed_total_in=parsed_total_in,
        parsed_total_out=parsed_total_out,
        importable_total_in=importable_total_in,
        importable_total_out=importable_total_out,
        excluded_total_in=excluded_total_in,
        excluded_total_out=excluded_total_out,
        invalid_total_in=invalid_total_in,
        invalid_total_out=invalid_total_out,
        expected_closing_balance=expected_closing,
        full_statement_matches=full_matches,
        importable_net=(importable_total_in - importable_total_out).quantize(Decimal("0.01")),
        excluded_net=(excluded_total_in - excluded_total_out).quantize(Decimal("0.01")),
        difference=difference,
    )


def _totals(
    candidates: list[ClassifiedCandidate],
    *classifications: CandidateClassification,
) -> tuple[Decimal, Decimal]:
    total_in = ZERO
    total_out = ZERO
    included = set(classifications)
    for candidate in candidates:
        if candidate.classification not in included or candidate.row.amount is None:
            continue
        if candidate.is_income is True:
            total_in += candidate.row.amount
        else:
            total_out += candidate.row.amount
    return total_in.quantize(Decimal("0.01")), total_out.quantize(Decimal("0.01"))
