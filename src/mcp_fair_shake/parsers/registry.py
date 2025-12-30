"""Parser registry for dependency injection."""

from mcp_fair_shake.parsers.base import LegislationParser


class ParserRegistry:
    """Registry of available legislation parsers."""

    def __init__(self) -> None:
        """Initialize empty parser registry."""
        self.parsers: list[LegislationParser] = []

    def register(self, parser: LegislationParser) -> None:
        """Register a parser.

        Args:
            parser: Parser implementing LegislationParser protocol
        """
        self.parsers.append(parser)

    def get_parser(self, url: str, content_type: str) -> LegislationParser:
        """Get appropriate parser for given URL and content type.

        Args:
            url: Source URL
            content_type: Content type

        Returns:
            Parser that can handle this content

        Raises:
            ValueError: If no parser found
        """
        for parser in self.parsers:
            if parser.can_parse(url, content_type):
                return parser

        raise ValueError(f"No parser found for {url} ({content_type})")
