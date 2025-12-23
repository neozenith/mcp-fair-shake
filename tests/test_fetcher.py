"""Tests for legislation fetcher."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from mcp_fair_shake.cache import CacheManager
from mcp_fair_shake.canonical_id import CanonicalID
from mcp_fair_shake.fetcher import (
    LEGISLATION_SOURCES,
    LegislationFetcher,
    LegislationFetchError,
)


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def cache_manager(temp_cache_dir: Path) -> CacheManager:
    """Create a cache manager with temporary directory."""
    return CacheManager(base_dir=temp_cache_dir)


@pytest.fixture
def fetcher(cache_manager: CacheManager) -> LegislationFetcher:
    """Create a legislation fetcher."""
    return LegislationFetcher(cache_manager=cache_manager)


class TestLegislationFetcher:
    """Test legislation fetcher functionality."""

    def test_initialization(self, cache_manager: CacheManager) -> None:
        """Test fetcher initialization."""
        fetcher = LegislationFetcher(cache_manager=cache_manager)
        assert fetcher.cache_manager is cache_manager
        assert fetcher.max_retries == 3
        assert fetcher.retry_delay == 1.0

    def test_is_cached_false_initially(self, fetcher: LegislationFetcher) -> None:
        """Test that legislation is not cached initially."""
        assert fetcher.is_cached("/au-victoria/ohs/2004") is False

    def test_is_cached_true_after_caching(
        self, fetcher: LegislationFetcher, cache_manager: CacheManager
    ) -> None:
        """Test that is_cached returns True after caching."""
        canonical = CanonicalID("au-victoria", "ohs", "2004")
        cache_manager.write_content(canonical, "Test content", "https://example.com")

        assert fetcher.is_cached("/au-victoria/ohs/2004") is True

    def test_is_cached_invalid_id(self, fetcher: LegislationFetcher) -> None:
        """Test is_cached with invalid ID."""
        assert fetcher.is_cached("/invalid/id") is False

    def test_get_source_info_valid(self, fetcher: LegislationFetcher) -> None:
        """Test getting source info for valid legislation."""
        info = fetcher.get_source_info("/au-victoria/ohs/2004")
        assert info is not None
        assert "url" in info
        assert "title" in info
        assert "Occupational Health" in info["title"]

    def test_get_source_info_invalid(self, fetcher: LegislationFetcher) -> None:
        """Test getting source info for invalid ID."""
        info = fetcher.get_source_info("/invalid/id")
        assert info is None

    def test_fetch_invalid_canonical_id(self, fetcher: LegislationFetcher) -> None:
        """Test fetching with invalid canonical ID."""
        with pytest.raises(ValueError, match="Invalid canonical ID"):
            fetcher.fetch("/invalid/id")

    def test_fetch_unsupported_legislation(self, fetcher: LegislationFetcher) -> None:
        """Test fetching unsupported legislation."""
        # Use a valid code type and year that's not configured in LEGISLATION_SOURCES
        with pytest.raises(LegislationFetchError, match="No source URL configured"):
            fetcher.fetch("/au-victoria/lsl/2020")  # LSL exists but 2020 version is not configured

    def test_fetch_from_cache(
        self, fetcher: LegislationFetcher, cache_manager: CacheManager
    ) -> None:
        """Test fetching from cache when available."""
        canonical = CanonicalID("au-victoria", "ohs", "2004")
        test_content = "Cached legislation content"
        cache_manager.write_content(canonical, test_content, "https://example.com")

        # Fetch should return cached content without HTTP request
        content = fetcher.fetch("/au-victoria/ohs/2004")
        assert content == test_content

    @patch("mcp_fair_shake.fetcher.httpx.Client")
    def test_fetch_with_http_download(
        self,
        mock_client_class: Mock,
        fetcher: LegislationFetcher,
    ) -> None:
        """Test fetching with HTTP download."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.text = "Downloaded legislation content"
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Replace fetcher's client with mock
        fetcher.client = mock_client

        # Fetch (should download since not cached)
        content = fetcher.fetch("/au-victoria/ohs/2004", force=True)
        assert content == "Downloaded legislation content"

        # Verify it was cached
        assert fetcher.is_cached("/au-victoria/ohs/2004") is True

    @patch("mcp_fair_shake.fetcher.httpx.Client")
    def test_fetch_http_error(
        self,
        mock_client_class: Mock,
        fetcher: LegislationFetcher,
    ) -> None:
        """Test fetching with HTTP error."""
        # Mock HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        fetcher.client = mock_client
        fetcher.max_retries = 1  # Reduce retries for faster test

        # Should raise LegislationFetchError after retries
        with pytest.raises(LegislationFetchError, match="HTTP error 404"):
            fetcher.fetch("/au-victoria/ohs/2004", force=True)

    def test_context_manager(self, cache_manager: CacheManager) -> None:
        """Test fetcher as context manager."""
        with LegislationFetcher(cache_manager=cache_manager) as fetcher:
            assert fetcher is not None

        # Client should be closed after exiting context

    def test_legislation_sources_configured(self) -> None:
        """Test that P0 legislation sources are configured."""
        assert "/au-federal/fwa/2009" in LEGISLATION_SOURCES
        assert "/au-victoria/ohs/2004" in LEGISLATION_SOURCES
        assert "/au-victoria/eoa/2010" in LEGISLATION_SOURCES

        # Check structure
        for _canonical_id, info in LEGISLATION_SOURCES.items():
            assert "url" in info
            assert "title" in info
            assert info["url"].startswith("https://")
