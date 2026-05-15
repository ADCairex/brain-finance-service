from datetime import date
from decimal import Decimal

from src.api.services.statement_import.classifier import classify_row, classify_rows
from src.api.services.statement_import.fingerprint import transaction_fingerprint
from src.api.services.statement_import.reconciler import reconcile_statement
from src.api.services.statement_import.trade_republic import TradeRepublicPdfParser
from src.api.services.statement_import.types import CandidateClassification, ParsedStatementRow, StatementProvider

SAMPLE_TEXT = """
TRADE REPUBLIC BANK GMBH, SUCURSAL EN ESPAÑA C/ VELAZQUEZ 50 - PLANTA 5, MADRID 28001 - MADRID
ANGEL MARTÍNEZ GUARDIOLA FECHA 01 sept 2025 - 21 abr 2026
RESUMEN DE ESTADO DE CUENTA
PRODUCTO BALANCE INICIAL ENTRADA DE DINERO SALIDA DE DINERO BALANCE FINAL
Cuenta corriente 4.093,14 € 1.806,37 € 418,34 € 5.481,17 €
TRANSACCIONES DE CUENTA
FECHA TIPO DESCRIPCIÓN ENTRADA DE DINERO SALIDA DE DINERO BALANCE
01 sept
Interés Interest payment 3,88 € 4.097,02 €
2025
07 sept Transacción
MERCADONA NOVELDA 17,50 € 4.079,52 €
2025 con tarjeta
08 sept
Transferencia Outgoing transfer for Ángel Caixabank 300,00 € 3.779,52 €
2025
09 sept Savings plan execution IE00B5BMR087 iShares VII plc - iShares Core S&P
Operar 0,84 € 3.778,68 €
2025 500 UCITS ETF USD (Acc), quantity: 0.001420
26 sept
Transferencia Incoming transfer from ANGEL MARTINEZ GUARDIOLA 1.800,00 € 5.578,68 €
2025
02 oct
Bonificación Bonus del 1% en Private Markets 2,49 € 5.581,17 €
2025
05 oct
Transferencia Outgoing transfer for ANGEL MARTINEZ GUARDIOLA 100,00 € 5.481,17 €
2025
RESUMEN DEL BALANCE
"""


def test_trade_republic_text_parser_extracts_summary_and_rows() -> None:
    statement = TradeRepublicPdfParser().parse_text(SAMPLE_TEXT)

    assert statement.provider == StatementProvider.TRADE_REPUBLIC
    assert statement.summary.opening_balance == Decimal("4093.14")
    assert statement.summary.total_in == Decimal("1806.37")
    assert statement.summary.total_out == Decimal("418.34")
    assert statement.summary.closing_balance == Decimal("5481.17")
    assert statement.summary.start_date == date(2025, 9, 1)
    assert statement.summary.end_date == date(2026, 4, 21)
    assert len(statement.rows) == 7
    assert statement.rows[1].transaction_date == date(2025, 9, 7)
    assert statement.rows[1].raw_type == "Transacción con tarjeta"
    assert statement.rows[1].description == "MERCADONA NOVELDA"
    assert statement.rows[1].amount == Decimal("17.50")
    assert statement.rows[1].balance_after == Decimal("4079.52")
    assert "MERCADONA NOVELDA" in statement.rows[1].raw_text


def test_classifier_marks_cash_excluded_duplicate_and_invalid_rows() -> None:
    parser = TradeRepublicPdfParser()
    statement = parser.parse_text(SAMPLE_TEXT)
    existing = {
        transaction_fingerprint(
            provider=StatementProvider.TRADE_REPUBLIC.value,
            transaction_date=date(2025, 9, 7),
            amount=Decimal("17.50"),
            description="MERCADONA NOVELDA",
            account_id=10,
        )
    }

    classified = classify_rows(statement.rows, account_id=10, existing_fingerprints=existing)

    assert classified[0].classification == CandidateClassification.IMPORTABLE
    assert classified[0].is_income is True
    assert classified[1].classification == CandidateClassification.DUPLICATE
    assert classified[2].classification == CandidateClassification.EXCLUDED
    assert classified[2].reason == "Internal or suspected transfer"
    assert classified[3].classification == CandidateClassification.EXCLUDED
    assert classified[3].reason == "Investment/trading operation"
    assert classified[5].classification == CandidateClassification.IMPORTABLE
    assert classified[5].is_income is True

    invalid = classify_row(
        ParsedStatementRow(99, None, "Transacción", "Broken row", Decimal("1.00"), None, "Broken row"),
        account_id=10,
    )
    assert invalid.classification == CandidateClassification.INVALID
    assert invalid.reason == "Missing transaction date"


def test_reconciler_separates_statement_importable_and_excluded_totals() -> None:
    statement = TradeRepublicPdfParser().parse_text(SAMPLE_TEXT)
    classified = classify_rows(statement.rows)

    result = reconcile_statement(statement, classified)

    assert result.full_statement_matches is True
    assert result.statement_total_in == Decimal("1806.37")
    assert result.statement_total_out == Decimal("418.34")
    assert result.importable_total_in == Decimal("6.37")
    assert result.importable_total_out == Decimal("17.50")
    assert result.excluded_total_in == Decimal("1800.00")
    assert result.excluded_total_out == Decimal("400.84")
    assert result.importable_net == Decimal("-11.13")
    assert result.excluded_net == Decimal("1399.16")
    assert result.difference == Decimal("0.00")


def test_transaction_fingerprint_is_stable_and_normalized() -> None:
    first = transaction_fingerprint(
        provider="trade_republic",
        transaction_date=date(2025, 9, 7),
        amount=Decimal("17.5"),
        description="  MÉRCADONA   Novelda ",
        account_id=1,
    )
    second = transaction_fingerprint(
        provider="TRADE_REPUBLIC",
        transaction_date=date(2025, 9, 7),
        amount=Decimal("17.50"),
        description="mercadona novelda",
        account_id=1,
    )
    different_account = transaction_fingerprint(
        provider="trade_republic",
        transaction_date=date(2025, 9, 7),
        amount=Decimal("17.50"),
        description="mercadona novelda",
        account_id=2,
    )

    assert first == second
    assert first != different_account
    assert len(first) == 64
