from datetime import date
from decimal import Decimal

from src.api.services.statement_import.types import (
    ParsedStatement,
    ParsedStatementRow,
    StatementProvider,
    StatementSummary,
)


def _statement(
    *, total_out: Decimal = Decimal("17.50"), closing_balance: Decimal = Decimal("982.50")
) -> ParsedStatement:
    return ParsedStatement(
        provider=StatementProvider.TRADE_REPUBLIC,
        summary=StatementSummary(
            provider=StatementProvider.TRADE_REPUBLIC,
            start_date=date(2025, 9, 1),
            end_date=date(2025, 9, 30),
            opening_balance=Decimal("1000.00"),
            total_in=Decimal("0.00"),
            total_out=total_out,
            closing_balance=closing_balance,
        ),
        rows=[
            ParsedStatementRow(
                1,
                date(2025, 9, 7),
                "Transacción con tarjeta",
                "MERCADONA NOVELDA",
                Decimal("17.50"),
                Decimal("982.50"),
                "07 sept 2025 Transacción con tarjeta MERCADONA NOVELDA 17,50 € 982,50 €",
            ),
            ParsedStatementRow(
                2,
                date(2025, 9, 8),
                "Transferencia",
                "Outgoing transfer for Ángel Caixabank",
                Decimal("300.00"),
                Decimal("682.50"),
                "08 sept 2025 Transferencia Outgoing transfer for Ángel Caixabank 300,00 € 682,50 €",
            ),
        ],
        raw_text="trade republic statement",
    )


def _upload(client, account_id: int, monkeypatch, statement: ParsedStatement | None = None):
    monkeypatch.setattr(
        "src.api.endpoints.imports.parse_pdf_bytes",
        lambda parser, pdf_bytes: statement or _statement(),
    )
    return client.post(
        "/api/imports/sessions",
        data={"provider": "trade_republic", "account_id": str(account_id)},
        files={"file": ("statement.pdf", b"%PDF-1.4", "application/pdf")},
    )


def test_upload_creates_session_candidates_only(client, account, monkeypatch) -> None:
    response = _upload(client, account["id"], monkeypatch)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "parsed"
    assert payload["counts"] == {"total": 2, "importable": 1, "excluded": 1, "duplicate": 0, "invalid": 0}
    assert payload["reconciliation"]["status"] == "mismatch"
    assert payload["candidates"][1]["classification"] == "excluded"
    assert client.get("/api/transactions").json() == []


def test_preview_reloads_excluded_rows(client, account, monkeypatch) -> None:
    upload = _upload(client, account["id"], monkeypatch).json()

    response = client.get(f"/api/imports/sessions/{upload['id']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["counts"]["excluded"] == 1
    assert any(candidate["exclusion_reason"] == "Internal or suspected transfer" for candidate in payload["candidates"])


def test_confirm_creates_transaction_for_selected_importable_row(client, account, monkeypatch) -> None:
    upload = _upload(client, account["id"], monkeypatch).json()
    importable_id = next(
        candidate["id"] for candidate in upload["candidates"] if candidate["classification"] == "importable"
    )

    response = client.post(
        f"/api/imports/sessions/{upload['id']}/confirm",
        json={"candidate_ids": [importable_id], "acknowledge_reconciliation_warning": True},
    )

    assert response.status_code == 200
    assert response.json()["imported_count"] == 1
    transactions = client.get("/api/transactions").json()
    assert len(transactions) == 1
    assert transactions[0]["description"] == "MERCADONA NOVELDA"


def test_confirm_skips_duplicate_fingerprint_on_second_session(client, account, monkeypatch) -> None:
    first_upload = _upload(client, account["id"], monkeypatch).json()
    first_importable_id = next(
        candidate["id"] for candidate in first_upload["candidates"] if candidate["classification"] == "importable"
    )
    client.post(
        f"/api/imports/sessions/{first_upload['id']}/confirm",
        json={"candidate_ids": [first_importable_id], "acknowledge_reconciliation_warning": True},
    )

    second_upload = _upload(client, account["id"], monkeypatch).json()

    assert second_upload["counts"]["duplicate"] == 1
    duplicate_id = next(
        candidate["id"] for candidate in second_upload["candidates"] if candidate["classification"] == "duplicate"
    )
    response = client.post(
        f"/api/imports/sessions/{second_upload['id']}/confirm",
        json={"candidate_ids": [duplicate_id], "acknowledge_reconciliation_warning": True},
    )

    assert response.status_code == 422
    assert len(client.get("/api/transactions").json()) == 1


def test_upload_links_duplicate_candidate_to_existing_transaction(client, account, monkeypatch) -> None:
    first_upload = _upload(client, account["id"], monkeypatch).json()
    first_importable_id = next(
        candidate["id"] for candidate in first_upload["candidates"] if candidate["classification"] == "importable"
    )
    first_confirm = client.post(
        f"/api/imports/sessions/{first_upload['id']}/confirm",
        json={"candidate_ids": [first_importable_id], "acknowledge_reconciliation_warning": True},
    ).json()

    second_upload = _upload(client, account["id"], monkeypatch).json()
    duplicate = next(
        candidate for candidate in second_upload["candidates"] if candidate["classification"] == "duplicate"
    )

    assert duplicate["duplicate_transaction_id"] == first_confirm["transaction_ids"][0]


def test_confirm_requires_reconciliation_warning_acknowledgement(client, account, monkeypatch) -> None:
    upload = _upload(client, account["id"], monkeypatch, _statement(total_out=Decimal("1.00"))).json()
    importable_id = next(
        candidate["id"] for candidate in upload["candidates"] if candidate["classification"] == "importable"
    )

    response = client.post(f"/api/imports/sessions/{upload['id']}/confirm", json={"candidate_ids": [importable_id]})

    assert response.status_code == 409
    assert response.json()["detail"] == "reconciliation_warning_acknowledgement_required"


def test_confirm_allows_reconciliation_warning_when_acknowledged(client, account, monkeypatch) -> None:
    upload = _upload(client, account["id"], monkeypatch, _statement(total_out=Decimal("1.00"))).json()
    importable_id = next(
        candidate["id"] for candidate in upload["candidates"] if candidate["classification"] == "importable"
    )

    response = client.post(
        f"/api/imports/sessions/{upload['id']}/confirm",
        json={"candidate_ids": [importable_id], "acknowledge_reconciliation_warning": True},
    )

    assert response.status_code == 200
    assert response.json()["imported_count"] == 1


def test_confirm_rejects_invalid_selected_candidate_without_creating_transaction(client, account, monkeypatch) -> None:
    statement = ParsedStatement(
        provider=StatementProvider.TRADE_REPUBLIC,
        summary=StatementSummary(
            provider=StatementProvider.TRADE_REPUBLIC,
            start_date=date(2025, 9, 1),
            end_date=date(2025, 9, 30),
            opening_balance=Decimal("1000.00"),
            total_in=Decimal("0.00"),
            total_out=Decimal("0.00"),
            closing_balance=Decimal("1000.00"),
        ),
        rows=[
            ParsedStatementRow(
                1,
                None,
                "Transacción con tarjeta",
                "MERCADONA NOVELDA",
                Decimal("17.50"),
                Decimal("982.50"),
                "Transacción con tarjeta MERCADONA NOVELDA 17,50 € 982,50 €",
            )
        ],
        raw_text="trade republic statement",
    )
    upload = _upload(client, account["id"], monkeypatch, statement).json()
    invalid_id = next(candidate["id"] for candidate in upload["candidates"] if candidate["classification"] == "invalid")

    response = client.post(
        f"/api/imports/sessions/{upload['id']}/confirm",
        json={"candidate_ids": [invalid_id], "acknowledge_reconciliation_warning": True},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "selected_rows_not_importable"
    assert client.get("/api/transactions").json() == []


def test_confirm_is_idempotent_after_success(client, account, monkeypatch) -> None:
    upload = _upload(client, account["id"], monkeypatch).json()
    importable_id = next(
        candidate["id"] for candidate in upload["candidates"] if candidate["classification"] == "importable"
    )

    first = client.post(
        f"/api/imports/sessions/{upload['id']}/confirm",
        json={"candidate_ids": [importable_id], "acknowledge_reconciliation_warning": True},
    )
    second = client.post(
        f"/api/imports/sessions/{upload['id']}/confirm",
        json={"candidate_ids": [importable_id], "acknowledge_reconciliation_warning": True},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["imported_count"] == 0
    assert len(client.get("/api/transactions").json()) == 1
