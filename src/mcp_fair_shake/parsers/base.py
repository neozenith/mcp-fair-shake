"""Base protocol for legislation parsers."""

from typing import Protocol

from mcp_fair_shake.models import Act


class LegislationParser(Protocol):
    """Protocol for legislation parsers using dependency injection."""

    def can_parse(self, url: str, content_type: str) -> bool:
        """Check if this parser can handle the given URL and content type.

        Args:
            url: Source URL of the legislation
            content_type: MIME type or description of content

        Returns:
            True if this parser can handle this content
        """
        ...

    def parse(self, content: bytes, metadata: dict) -> Act:
        """Parse content into structured Act with full hierarchy.

        Args:
            content: Raw legislation content (text or binary)
            metadata: Metadata dict with jurisdiction, year, canonical_id, etc.

        Returns:
            Act object with full hierarchy (Parts, Divisions, Sections, etc.)

        Raises:
            ValueError: If content cannot be parsed
        """
        ...
