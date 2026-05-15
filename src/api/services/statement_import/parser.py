from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol

from .types import ParsedStatement, StatementProvider


class StatementParser(Protocol):
    provider: StatementProvider

    def parse_text(self, text: str) -> ParsedStatement:
        raise NotImplementedError

    def parse_pdf(self, pdf_path: Path) -> ParsedStatement:
        raise NotImplementedError


def parse_pdf_bytes(parser: StatementParser, pdf_bytes: bytes) -> ParsedStatement:
    """Parse in-memory PDF bytes with parsers that currently accept a file path."""
    with NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(pdf_bytes)
        tmp.flush()
        return parser.parse_pdf(Path(tmp.name))
