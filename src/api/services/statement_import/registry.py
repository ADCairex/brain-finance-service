from .parser import StatementParser
from .types import StatementProvider


class StatementParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[StatementProvider, StatementParser] = {}

    def register(self, parser: StatementParser) -> None:
        self._parsers[parser.provider] = parser

    def get(self, provider: StatementProvider | str) -> StatementParser:
        normalized_provider = provider if isinstance(provider, StatementProvider) else StatementProvider(provider)
        try:
            return self._parsers[normalized_provider]
        except KeyError as exc:
            raise ValueError(f"No statement parser registered for provider '{normalized_provider}'") from exc


parser_registry = StatementParserRegistry()
