import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from .types import ParsedStatement, ParsedStatementRow, StatementProvider, StatementSummary

MONTHS = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sept": 9,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}

TRANSACTION_START_RE = re.compile(
    r"^(?P<day>\d{2}) (?P<month>ene|feb|mar|abr|may|jun|jul|ago|sept|sep|oct|nov|dic)(?:\s+(?P<rest>.*))?$",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"^(?P<year>20\d{2})(?:\s+(?P<trailing>.*))?$")
MONEY_RE = re.compile(r"(?P<amount>-?\d{1,3}(?:\.\d{3})*,\d{2})\s*[^\d\s]?", re.IGNORECASE)
SUMMARY_RE = re.compile(
    r"Cuenta corriente\s+(?P<opening>\d{1,3}(?:\.\d{3})*,\d{2})\s+[^\d]+"
    r"(?P<in>\d{1,3}(?:\.\d{3})*,\d{2})\s+[^\d]+"
    r"(?P<out>\d{1,3}(?:\.\d{3})*,\d{2})\s+[^\d]+"
    r"(?P<closing>\d{1,3}(?:\.\d{3})*,\d{2})",
    re.IGNORECASE,
)
PERIOD_RE = re.compile(
    r"FECHA\s+(?P<start_day>\d{2}) (?P<start_month>\w+) (?P<start_year>20\d{2})\s+-\s+"
    r"(?P<end_day>\d{2}) (?P<end_month>\w+) (?P<end_year>20\d{2})",
    re.IGNORECASE,
)
FOOTER_PREFIXES = (
    "Trade Republic Bank GmbH",
    "C/ Velazquez",
    "28001, Madrid",
    "NIF:",
    "Thomas Pischke",
    "Creado en",
    "TRADE REPUBLIC BANK GMBH",
    "FECHA TIPO DESCRIPCI",
)
STOP_PREFIXES = ("RESUMEN DEL BALANCE", "NOTAS SOBRE EL EXTRACTO")


class TradeRepublicPdfParser:
    provider = StatementProvider.TRADE_REPUBLIC

    def parse_pdf(self, pdf_path: Path) -> ParsedStatement:
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError("pdfplumber is required to parse Trade Republic PDF statements") from exc

        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return self.parse_text(text)

    def parse_text(self, text: str) -> ParsedStatement:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        summary = self._parse_summary(text)
        blocks = self._transaction_blocks(lines)
        rows = [self._parse_block(index, block) for index, block in enumerate(blocks, start=1)]
        return ParsedStatement(provider=self.provider, summary=summary, rows=rows, raw_text=text)

    def _parse_summary(self, text: str) -> StatementSummary:
        period_match = PERIOD_RE.search(text)
        summary_match = SUMMARY_RE.search(text)
        return StatementSummary(
            provider=self.provider,
            start_date=self._date_from_period(period_match, "start") if period_match else None,
            end_date=self._date_from_period(period_match, "end") if period_match else None,
            opening_balance=parse_money(summary_match.group("opening")) if summary_match else None,
            total_in=parse_money(summary_match.group("in")) if summary_match else None,
            total_out=parse_money(summary_match.group("out")) if summary_match else None,
            closing_balance=parse_money(summary_match.group("closing")) if summary_match else None,
        )

    def _date_from_period(self, match: re.Match[str], prefix: str) -> date | None:
        month = MONTHS.get(match.group(f"{prefix}_month").casefold())
        if month is None:
            return None
        return date(int(match.group(f"{prefix}_year")), month, int(match.group(f"{prefix}_day")))

    def _transaction_blocks(self, lines: list[str]) -> list[list[str]]:
        blocks: list[list[str]] = []
        current: list[str] = []
        in_transactions = False
        for line in lines:
            if line == "TRANSACCIONES DE CUENTA":
                in_transactions = True
                continue
            if not in_transactions:
                continue
            if line.startswith(STOP_PREFIXES):
                break
            if self._is_noise(line):
                continue
            if TRANSACTION_START_RE.match(line):
                if current:
                    blocks.append(current)
                current = [line]
            elif current:
                current.append(line)
        if current:
            blocks.append(current)
        return blocks

    def _is_noise(self, line: str) -> bool:
        return line.startswith(FOOTER_PREFIXES)

    def _parse_block(self, source_order: int, block: list[str]) -> ParsedStatementRow:
        raw_text = "\n".join(block)
        start_match = TRANSACTION_START_RE.match(block[0])
        if start_match is None:
            return ParsedStatementRow(source_order, None, "", raw_text, None, None, raw_text)

        year, trailing_lines = self._extract_year_and_trailing(block[1:])
        transaction_date = self._row_date(start_match, year)
        content_parts = [start_match.group("rest") or "", *trailing_lines]
        content = " ".join(part for part in content_parts if part).strip()
        money_values = [parse_money(match.group("amount")) for match in MONEY_RE.finditer(content)]
        amount = money_values[-2] if len(money_values) >= 2 else None
        balance_after = money_values[-1] if money_values else None
        content_without_money = MONEY_RE.sub("", content)
        raw_type, description = self._split_type_description(content_without_money)
        return ParsedStatementRow(
            source_order=source_order,
            transaction_date=transaction_date,
            raw_type=raw_type,
            description=description,
            amount=amount,
            balance_after=balance_after,
            raw_text=raw_text,
            provenance=f"trade_republic:block:{source_order}",
        )

    def _extract_year_and_trailing(self, lines: list[str]) -> tuple[int | None, list[str]]:
        trailing: list[str] = []
        year: int | None = None
        for line in lines:
            match = YEAR_RE.match(line)
            if match:
                year = int(match.group("year"))
                if match.group("trailing"):
                    trailing.append(match.group("trailing"))
            else:
                trailing.append(line)
        return year, trailing

    def _row_date(self, start_match: re.Match[str], year: int | None) -> date | None:
        month = MONTHS.get(start_match.group("month").casefold())
        if year is None or month is None:
            return None
        return date(year, month, int(start_match.group("day")))

    def _split_type_description(self, content: str) -> tuple[str, str]:
        cleaned = re.sub(r"\s+", " ", content).strip(" -")
        known_types = [
            "Transacción con tarjeta",
            "Transacción",
            "Transferencia",
            "Interés",
            "Operar",
            "Bonificación",
            "Savings plan execution",
            "Buy trade",
            "Sell trade",
        ]
        for raw_type in known_types:
            if cleaned.casefold().startswith(raw_type.casefold()):
                description = cleaned[len(raw_type) :].strip(" -") or raw_type
                if raw_type == "Transacción" and description.endswith(" con tarjeta"):
                    description = description.removesuffix(" con tarjeta").strip()
                    raw_type = "Transacción con tarjeta"
                return raw_type, description
            if raw_type.casefold() in cleaned.casefold():
                index = cleaned.casefold().index(raw_type.casefold())
                description = (cleaned[:index] + " " + cleaned[index + len(raw_type) :]).strip(" -")
                return raw_type, description or raw_type
        first, _, rest = cleaned.partition(" ")
        return first, rest or cleaned


def parse_money(value: str) -> Decimal:
    return Decimal(value.replace(".", "").replace(",", "."))
