from pathlib import Path
from typing import Protocol

from .types import ParsedStatement, StatementProvider


class StatementParser(Protocol):
    provider: StatementProvider

    def parse_text(self, text: str) -> ParsedStatement:
        """Parse already extracted statement text."""

    def parse_pdf(self, pdf_path: Path) -> ParsedStatement:
        """Extract text from a PDF and parse it."""
