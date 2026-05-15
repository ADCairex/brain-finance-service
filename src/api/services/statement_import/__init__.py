"""Statement import domain services."""

from .registry import parser_registry
from .trade_republic import TradeRepublicPdfParser

parser_registry.register(TradeRepublicPdfParser())
