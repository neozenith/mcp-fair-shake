"""Tests for Playwright-based legislation fetching - TDD approach.

These tests define what the async Playwright fetcher MUST do.
Tests written FIRST, then implementation.
"""

import pytest

from mcp_fair_shake.fetcher import LegislationFetcher


class TestPlaywrightFetching:
    """Test async Playwright fetching for JavaScript-rendered sites."""

    @pytest.mark.asyncio
    async def test_fetch_victorian_legislation_has_real_sections(self) -> None:
        """Test that Victorian legislation contains actual section content.

        Victorian sites use JavaScript rendering. This test will FAIL
        until Playwright rendering is implemented.
        """
        fetcher = LegislationFetcher()

        # Fetch OHS Act using Playwright rendering
        content = await fetcher.fetch_async("/au-victoria/ohs/2004", use_playwright=True)

        # Must NOT be minimal (>5KB expected)
        assert len(content) > 5000, f"Content too short: {len(content)} bytes"

        # Must contain actual section content
        assert "section" in content.lower() or "part" in content.lower()

        # Must NOT be just navigation/metadata
        assert "Skip to main content" not in content or len(content) > 10000

    @pytest.mark.asyncio
    async def test_fetch_with_playwright_extracts_legislation_text(self) -> None:
        """Test Playwright extracts actual legislation, not just navigation."""
        fetcher = LegislationFetcher()

        content = await fetcher.fetch_async("/au-victoria/eoa/2010", use_playwright=True)

        # Should contain substantial content
        assert len(content) > 3000

        # Should have legislation structure
        assert any(keyword in content.lower() for keyword in ["act", "section", "part", "division"])

    @pytest.mark.asyncio
    async def test_fetch_async_without_playwright_uses_httpx(self) -> None:
        """Test that fetch_async without Playwright uses httpx (fast path)."""
        fetcher = LegislationFetcher()

        # Federal sites work fine with httpx
        content = await fetcher.fetch_async("/au-federal/fwa/2009", use_playwright=False)

        # Should get real content
        assert len(content) > 100000  # Fair Work Act is large
        assert "Fair Work" in content

    @pytest.mark.asyncio
    async def test_fetch_async_auto_detects_javascript_sites(self) -> None:
        """Test auto-detection of JavaScript sites."""
        fetcher = LegislationFetcher()

        # Victorian sites should auto-detect need for Playwright
        # This will initially fail, then pass when auto-detection is implemented
        content = await fetcher.fetch_async("/au-victoria/ohs/2004")

        # Should have substantial content (not just navigation)
        assert len(content) > 5000
