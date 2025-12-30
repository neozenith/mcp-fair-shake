"""Legislation parser module."""

from .base import LegislationParser
from .federal_text import FederalTextParser
from .registry import ParserRegistry
from .victorian_text import VictorianTextParser

__all__ = [
    "LegislationParser",
    "ParserRegistry",
    "FederalTextParser",
    "VictorianTextParser",
]
