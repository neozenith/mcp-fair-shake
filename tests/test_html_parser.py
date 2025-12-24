"""Tests for HTML parsing - CRITICAL BLOCKER.

These tests define what the HTML parser MUST do before it can be considered working.
"""

from mcp_fair_shake.fetcher import LegislationFetcher


class TestHtmlParsing:
    """Test HTML parsing extracts actual legislation content."""

    def test_parser_returns_real_content_not_placeholder(self) -> None:
        """Test that parser returns real content, not placeholder text.

        CRITICAL: This is the core bug - parser currently returns:
        "[PLACEHOLDER: HTML parsing not yet implemented]"

        This test will FAIL until real parsing is implemented.
        """
        fetcher = LegislationFetcher()

        # Sample HTML that simulates legislation.vic.gov.au structure
        sample_html = """
        <html>
        <body>
            <div class="content">
                <h1>Occupational Health and Safety Act 2004</h1>
                <div class="section">
                    <h2>Section 21</h2>
                    <p>Employers must ensure, so far as is reasonably practicable,
                    the health and safety of employees in the workplace.</p>
                </div>
            </div>
        </body>
        </html>
        """

        result = fetcher._parse_html_content(sample_html, "Test Act")

        # MUST NOT contain placeholder text
        assert "[PLACEHOLDER" not in result
        assert "HTML parsing not yet implemented" not in result

        # MUST contain actual content
        assert "Section 21" in result
        assert "Employers must ensure" in result
        assert "health and safety" in result

    def test_parser_extracts_section_headings(self) -> None:
        """Test parser preserves section structure."""
        fetcher = LegislationFetcher()

        sample_html = """
        <div class="act">
            <h2>Part 1 - Introduction</h2>
            <div class="section">
                <h3>Section 1 - Purpose</h3>
                <p>The purpose of this Act is...</p>
            </div>
            <div class="section">
                <h3>Section 2 - Definitions</h3>
                <p>In this Act, unless the contrary intention appears...</p>
            </div>
        </div>
        """

        result = fetcher._parse_html_content(sample_html, "Test Act")

        # Must preserve structure
        assert "Part 1" in result
        assert "Section 1" in result
        assert "Section 2" in result
        assert "Purpose" in result
        assert "Definitions" in result

    def test_parser_handles_empty_html(self) -> None:
        """Test parser handles empty/invalid HTML gracefully."""
        fetcher = LegislationFetcher()

        result = fetcher._parse_html_content("", "Empty Act")

        # Should return something indicating no content found
        assert result
        assert len(result) > 0

    def test_parser_removes_script_and_style(self) -> None:
        """Test parser removes JavaScript and CSS."""
        fetcher = LegislationFetcher()

        sample_html = """
        <html>
        <head>
            <script>alert('test');</script>
            <style>.test { color: red; }</style>
        </head>
        <body>
            <div>Real content here</div>
            <script>console.log('more js');</script>
        </body>
        </html>
        """

        result = fetcher._parse_html_content(sample_html, "Test Act")

        # Must NOT contain JavaScript or CSS
        assert "alert" not in result
        assert "console.log" not in result
        assert ".test" not in result
        assert "color: red" not in result

        # MUST contain real content
        assert "Real content" in result
