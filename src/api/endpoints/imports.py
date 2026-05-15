from collections.abc import Iterable
from decimal import Decimal
from hashlib import sha256

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user_id
from ..models import Account, StatementImportCandidate, StatementImportSession, Transaction
from ..schemas import (
    StatementImportCandidateOut,
    StatementImportConfirmOut,
    StatementImportConfirmRequest,
    StatementImportCountsOut,
    StatementImportReconciliationOut,
    StatementImportSessionOut,
)
from ..services.statement_import.classifier import classify_rows
from ..services.statement_import.parser import parse_pdf_bytes
from ..services.statement_import.reconciler import reconcile_statement
from ..services.statement_import.registry import parser_registry
from ..services.statement_import.types import CandidateClassification, ClassifiedCandidate, StatementProvider

router = APIRouter(tags=["imports"])

PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
WARNING_RECONCILIATION_STATUSES = {"warning", "mismatch"}


@router.post("/api/import/upload", response_model=StatementImportSessionOut)
@router.post("/api/imports/sessions", response_model=StatementImportSessionOut)
def create_import_session(
    provider: str = Form(...),
    account_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> StatementImportSessionOut:
    account = _get_user_account(db, account_id, user_id)
    parsed_provider = _parse_provider(provider)
    if file.content_type not in PDF_CONTENT_TYPES:
        raise HTTPException(status_code=422, detail="invalid_file_type")

    pdf_bytes = file.file.read()
    parser = parser_registry.get(parsed_provider)
    statement = parse_pdf_bytes(parser, pdf_bytes)
    existing_fingerprints = _existing_fingerprints(db, account.id)
    classified = classify_rows(
        statement.rows,
        provider=parsed_provider,
        account_id=account.id,
        existing_fingerprints=existing_fingerprints,
    )
    reconciliation = reconcile_statement(statement, classified)
    reconciliation_status = _reconciliation_status(reconciliation.full_statement_matches)
    session = StatementImportSession(
        user_id=user_id,
        account_id=account.id,
        provider=parsed_provider.value,
        source_filename=file.filename,
        source_file_hash=sha256(pdf_bytes).hexdigest(),
        status="parsed",
        statement_start_date=statement.summary.start_date,
        statement_end_date=statement.summary.end_date,
        opening_balance=statement.summary.opening_balance,
        closing_balance=statement.summary.closing_balance,
        statement_total_in=reconciliation.statement_total_in,
        statement_total_out=reconciliation.statement_total_out,
        reconciliation_status=reconciliation_status,
        reconciliation_notes=_reconciliation_notes(reconciliation_status),
    )
    db.add(session)
    db.flush()
    db.add_all(_candidate_model(db, session.id, account.id, candidate) for candidate in classified)
    db.commit()
    db.refresh(session)
    return _session_out(session)


@router.get("/api/import/{session_id}", response_model=StatementImportSessionOut)
@router.get("/api/imports/sessions/{session_id}", response_model=StatementImportSessionOut)
def get_import_session(
    session_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> StatementImportSessionOut:
    return _session_out(_get_user_session(db, session_id, user_id))


@router.post("/api/import/{session_id}/confirm", response_model=StatementImportConfirmOut)
@router.post("/api/imports/sessions/{session_id}/confirm", response_model=StatementImportConfirmOut)
def confirm_import_session(
    session_id: int,
    request: StatementImportConfirmRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> StatementImportConfirmOut:
    session = _get_user_session(db, session_id, user_id)
    if session.status == "confirmed":
        return StatementImportConfirmOut(session_id=session.id, imported_count=0, transaction_ids=[])
    if session.status != "parsed":
        raise HTTPException(status_code=409, detail="session_not_confirmable")
    if (
        session.reconciliation_status in WARNING_RECONCILIATION_STATUSES
        and not request.acknowledge_reconciliation_warning
    ):
        raise HTTPException(status_code=409, detail="reconciliation_warning_acknowledgement_required")

    selected_ids = set(request.candidate_ids)
    candidates = [candidate for candidate in session.candidates if candidate.id in selected_ids]
    if not candidates:
        raise HTTPException(status_code=422, detail="no_selected_eligible_rows")
    blocked = [
        candidate for candidate in candidates if candidate.classification != CandidateClassification.IMPORTABLE.value
    ]
    if blocked:
        raise HTTPException(status_code=422, detail="selected_rows_not_importable")

    transaction_ids: list[int] = []
    for candidate in candidates:
        if candidate.fingerprint and _transaction_exists_for_fingerprint(db, candidate.fingerprint):
            continue
        if candidate.transaction_date is None or candidate.amount is None or candidate.is_income is None:
            raise HTTPException(status_code=422, detail="selected_rows_not_importable")
        transaction = Transaction(
            description=candidate.description,
            amount=candidate.amount,
            category=candidate.category_hint or ("ingreso" if candidate.is_income else "otros"),
            date=candidate.transaction_date,
            is_income=candidate.is_income,
            notes=f"Imported from {session.provider} statement session {session.id}",
            account_id=session.account_id,
            import_fingerprint=candidate.fingerprint,
            source_import_candidate_id=candidate.id,
        )
        db.add(transaction)
        db.flush()
        transaction_ids.append(transaction.id)
    if not transaction_ids:
        raise HTTPException(status_code=422, detail="no_new_transactions_to_import")
    session.status = "confirmed"
    db.commit()
    return StatementImportConfirmOut(
        session_id=session.id,
        imported_count=len(transaction_ids),
        transaction_ids=transaction_ids,
    )


def _parse_provider(provider: str) -> StatementProvider:
    try:
        return StatementProvider(provider)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="unsupported_provider") from exc


def _get_user_account(db: Session, account_id: int, user_id: int) -> Account:
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == user_id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="account_not_found")
    return account


def _get_user_session(db: Session, session_id: int, user_id: int) -> StatementImportSession:
    session = (
        db.query(StatementImportSession)
        .filter(StatementImportSession.id == session_id, StatementImportSession.user_id == user_id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    return session


def _existing_fingerprints(db: Session, account_id: int) -> set[str]:
    rows = db.query(Transaction.import_fingerprint).filter(
        Transaction.account_id == account_id,
        Transaction.import_fingerprint.isnot(None),
    )
    return {fingerprint for (fingerprint,) in rows.all() if fingerprint}


def _transaction_exists_for_fingerprint(db: Session, fingerprint: str) -> bool:
    return db.query(Transaction.id).filter(Transaction.import_fingerprint == fingerprint).first() is not None


def _candidate_model(
    db: Session,
    session_id: int,
    account_id: int,
    candidate: ClassifiedCandidate,
) -> StatementImportCandidate:
    row = candidate.row
    return StatementImportCandidate(
        session_id=session_id,
        source_order=row.source_order,
        transaction_date=row.transaction_date,
        raw_type=row.raw_type,
        description=row.description,
        amount=row.amount,
        balance_after=row.balance_after,
        classification=candidate.classification.value,
        category_hint=candidate.category_hint,
        is_income=candidate.is_income,
        exclusion_reason=candidate.reason if candidate.classification == CandidateClassification.EXCLUDED else None,
        validation_error=candidate.reason if candidate.classification == CandidateClassification.INVALID else None,
        fingerprint=candidate.fingerprint,
        duplicate_transaction_id=_duplicate_transaction_id(db, account_id, candidate),
        raw_text=row.raw_text,
        provenance=row.provenance,
    )


def _duplicate_transaction_id(db: Session, account_id: int, candidate: ClassifiedCandidate) -> int | None:
    if candidate.classification != CandidateClassification.DUPLICATE or candidate.fingerprint is None:
        return None

    row = (
        db.query(Transaction.id)
        .filter(
            Transaction.account_id == account_id,
            Transaction.import_fingerprint == candidate.fingerprint,
        )
        .first()
    )
    return row[0] if row is not None else None


def _session_out(session: StatementImportSession) -> StatementImportSessionOut:
    candidates = sorted(session.candidates, key=lambda candidate: candidate.source_order)
    return StatementImportSessionOut(
        id=session.id,
        provider=session.provider,
        account_id=session.account_id,
        status=session.status,
        reconciliation=_reconciliation_out(session, candidates),
        counts=_counts_out(candidates),
        candidates=[StatementImportCandidateOut.model_validate(candidate) for candidate in candidates],
    )


def _reconciliation_out(
    session: StatementImportSession,
    candidates: Iterable[StatementImportCandidate],
) -> StatementImportReconciliationOut:
    totals = _candidate_totals(candidates)
    expected_closing = None
    difference = None
    if session.opening_balance is not None and session.closing_balance is not None:
        expected_closing = (session.opening_balance + totals["parsed_in"] - totals["parsed_out"]).quantize(
            Decimal("0.01")
        )
        difference = (session.closing_balance - expected_closing).quantize(Decimal("0.01"))
    return StatementImportReconciliationOut(
        status=session.reconciliation_status or "unknown",
        notes=session.reconciliation_notes,
        opening_balance=_float_or_none(session.opening_balance),
        closing_balance=_float_or_none(session.closing_balance),
        statement_total_in=float(session.statement_total_in or Decimal("0.00")),
        statement_total_out=float(session.statement_total_out or Decimal("0.00")),
        parsed_total_in=float(totals["parsed_in"]),
        parsed_total_out=float(totals["parsed_out"]),
        importable_total_in=float(totals["importable_in"]),
        importable_total_out=float(totals["importable_out"]),
        excluded_total_in=float(totals["excluded_in"]),
        excluded_total_out=float(totals["excluded_out"]),
        invalid_total_in=float(totals["invalid_in"]),
        invalid_total_out=float(totals["invalid_out"]),
        expected_closing_balance=_float_or_none(expected_closing),
        difference=_float_or_none(difference),
    )


def _counts_out(candidates: Iterable[StatementImportCandidate]) -> StatementImportCountsOut:
    items = list(candidates)
    return StatementImportCountsOut(
        total=len(items),
        importable=sum(
            1 for candidate in items if candidate.classification == CandidateClassification.IMPORTABLE.value
        ),
        excluded=sum(1 for candidate in items if candidate.classification == CandidateClassification.EXCLUDED.value),
        duplicate=sum(1 for candidate in items if candidate.classification == CandidateClassification.DUPLICATE.value),
        invalid=sum(1 for candidate in items if candidate.classification == CandidateClassification.INVALID.value),
    )


def _candidate_totals(candidates: Iterable[StatementImportCandidate]) -> dict[str, Decimal]:
    totals = {
        "parsed_in": Decimal("0.00"),
        "parsed_out": Decimal("0.00"),
        "importable_in": Decimal("0.00"),
        "importable_out": Decimal("0.00"),
        "excluded_in": Decimal("0.00"),
        "excluded_out": Decimal("0.00"),
        "invalid_in": Decimal("0.00"),
        "invalid_out": Decimal("0.00"),
    }
    for candidate in candidates:
        if candidate.amount is None:
            continue
        prefix = _totals_prefix(candidate.classification)
        if prefix is None:
            continue
        direction = "in" if candidate.is_income is True else "out"
        totals[f"{prefix}_{direction}"] += candidate.amount
        if candidate.classification in {
            CandidateClassification.IMPORTABLE.value,
            CandidateClassification.EXCLUDED.value,
        }:
            totals[f"parsed_{direction}"] += candidate.amount
    return {key: value.quantize(Decimal("0.01")) for key, value in totals.items()}


def _totals_prefix(classification: str) -> str | None:
    if classification == CandidateClassification.IMPORTABLE.value:
        return "importable"
    if classification == CandidateClassification.EXCLUDED.value:
        return "excluded"
    if classification == CandidateClassification.INVALID.value:
        return "invalid"
    return None


def _reconciliation_status(full_statement_matches: bool | None) -> str:
    if full_statement_matches is True:
        return "matched"
    if full_statement_matches is False:
        return "mismatch"
    return "warning"


def _reconciliation_notes(status: str) -> str | None:
    if status == "matched":
        return None
    return "Full statement reconciliation could not be matched exactly. Confirmation requires acknowledgement."


def _float_or_none(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None
