"""Integration tests for legislation fetcher - REAL downloads, NO MOCKS.

These tests actually download and parse legislation from official sources.
They may be slower but they test the real system end-to-end.
"""

import pytest

from mcp_fair_shake.fetcher import LegislationFetcher, LegislationFetchError


class TestFetcherIntegration:
    """Integration tests with real HTTP requests."""

    def test_fetch_federal_html_legislation(self) -> None:
        """Test fetching federal HTML legislation (Fair Work Act)."""
        fetcher = LegislationFetcher()

        # Fetch Fair Work Act (HTML source)
        content = fetcher.fetch("/au-federal/fwa/2009", force=True)

        # Should have substantial content
        assert len(content) > 100000  # Fair Work Act is large

        # Should contain actual legislation
        assert "Fair Work" in content
        assert "Part" in content or "Division" in content

        # Should be cached now
        assert fetcher.is_cached("/au-federal/fwa/2009")

        fetcher.close()

    def test_fetch_victorian_pdf_legislation(self) -> None:
        """Test fetching Victorian PDF legislation (OHS Act)."""
        fetcher = LegislationFetcher()

        # Fetch OHS Act (PDF source)
        content = fetcher.fetch("/au-victoria/ohs/2004", force=True)

        # Should have substantial content
        assert len(content) > 50000  # OHS Act is long

        # Should contain actual legislation with page markers
        assert "[Page" in content
        assert "Occupational Health" in content

        # Should be cached now
        assert fetcher.is_cached("/au-victoria/ohs/2004")

        fetcher.close()

    def test_fetch_invalid_url_raises_error(self) -> None:
        """Test that invalid legislation ID raises error."""
        fetcher = LegislationFetcher()

        with pytest.raises(ValueError, match="Invalid canonical ID"):
            fetcher.fetch("/invalid/format")

        fetcher.close()

    def test_fetch_unsupported_legislation_raises_error(self) -> None:
        """Test that unsupported legislation raises error."""
        fetcher = LegislationFetcher()

        with pytest.raises(LegislationFetchError, match="No source URL configured"):
            fetcher.fetch("/au-victoria/ohs/2099")  # Year 2099 doesn't exist

        fetcher.close()

    @pytest.mark.asyncio
    async def test_fetch_async_federal_html(self) -> None:
        """Test async fetching of federal HTML legislation."""
        fetcher = LegislationFetcher()

        # Fetch Fair Work Regulations (smaller than FWA)
        content = await fetcher.fetch_async("/au-federal/fwr/2009", force=True)

        # Should have content
        assert len(content) > 100  # At minimum

        # Should contain legislation
        assert "Fair Work" in content or "Regulation" in content

        fetcher.close()

    @pytest.mark.asyncio
    async def test_fetch_async_victorian_pdf(self) -> None:
        """Test async fetching of Victorian PDF legislation."""
        fetcher = LegislationFetcher()

        # Fetch Equal Opportunity Act (PDF)
        content = await fetcher.fetch_async("/au-victoria/eoa/2010", force=True)

        # Should have substantial content with page markers
        assert len(content) > 30000
        assert "[Page" in content
        assert "Equal Opportunity" in content

        fetcher.close()

    def test_fetch_from_cache_second_time(self) -> None:
        """Test that second fetch uses cache (no download)."""
        fetcher = LegislationFetcher()

        # First fetch (downloads)
        content1 = fetcher.fetch("/au-victoria/ohs/2004", force=False)

        # Second fetch (from cache)
        content2 = fetcher.fetch("/au-victoria/ohs/2004", force=False)

        # Should be identical
        assert content1 == content2
        assert len(content1) > 50000

        fetcher.close()
