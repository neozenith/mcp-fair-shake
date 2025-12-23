"""Tests for cache management."""

from pathlib import Path

import pytest

from mcp_fair_shake.cache import CacheManager, LegislationMetadata
from mcp_fair_shake.canonical_id import CanonicalID


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
def sample_canonical() -> CanonicalID:
    """Create a sample canonical ID."""
    return CanonicalID("au-victoria", "ohs", "2004")


class TestCacheManager:
    """Test cache manager functionality."""

    def test_get_cache_path(
        self, cache_manager: CacheManager, sample_canonical: CanonicalID
    ) -> None:
        """Test getting cache path."""
        path = cache_manager.get_cache_path(sample_canonical)
        assert path.name == "au-victoria"

    def test_get_content_path(
        self, cache_manager: CacheManager, sample_canonical: CanonicalID
    ) -> None:
        """Test getting content path."""
        path = cache_manager.get_content_path(sample_canonical)
        assert path.name == "ohs-2004.txt"
        assert "au-victoria" in str(path)

    def test_get_metadata_path(
        self, cache_manager: CacheManager, sample_canonical: CanonicalID
    ) -> None:
        """Test getting metadata path."""
        path = cache_manager.get_metadata_path(sample_canonical)
        assert path.name == "ohs-2004-metadata.json"

    def test_get_checksum_path(
        self, cache_manager: CacheManager, sample_canonical: CanonicalID
    ) -> None:
        """Test getting checksum path."""
        path = cache_manager.get_checksum_path(sample_canonical)
        assert path.name == "ohs-2004.checksum"

    def test_exists_false_initially(
        self, cache_manager: CacheManager, sample_canonical: CanonicalID
    ) -> None:
        """Test that content doesn't exist initially."""
        assert cache_manager.exists(sample_canonical) is False

    def test_write_and_read_content(
        self, cache_manager: CacheManager, sample_canonical: CanonicalID
    ) -> None:
        """Test writing and reading content."""
        test_content = "Test legislation content"
        source_url = "https://example.com/ohs-2004"

        # Write content
        cache_manager.write_content(
            sample_canonical, test_content, source_url, title="OHS Act 2004"
        )

        # Check it exists
        assert cache_manager.exists(sample_canonical) is True

        # Read content
        content = cache_manager.read_content(sample_canonical)
        assert content == test_content

    def test_read_nonexistent_content(
        self, cache_manager: CacheManager, sample_canonical: CanonicalID
    ) -> None:
        """Test reading non-existent content returns None."""
        content = cache_manager.read_content(sample_canonical)
        assert content is None

    def test_write_creates_metadata(
        self, cache_manager: CacheManager, sample_canonical: CanonicalID
    ) -> None:
        """Test that writing content creates metadata."""
        test_content = "Test content"
        source_url = "https://example.com/test"

        cache_manager.write_content(sample_canonical, test_content, source_url)

        # Read metadata
        metadata = cache_manager.read_metadata(sample_canonical)
        assert metadata is not None
        assert metadata.canonical_id == "/au-victoria/ohs/2004"
        assert metadata.source_url == source_url
        assert metadata.jurisdiction == "au-victoria"

    def test_verify_checksum_valid(
        self, cache_manager: CacheManager, sample_canonical: CanonicalID
    ) -> None:
        """Test checksum verification with valid content."""
        test_content = "Test content"
        source_url = "https://example.com/test"

        cache_manager.write_content(sample_canonical, test_content, source_url)

        # Verify checksum
        assert cache_manager.verify_checksum(sample_canonical) is True

    def test_verify_checksum_invalid(
        self, cache_manager: CacheManager, sample_canonical: CanonicalID
    ) -> None:
        """Test checksum verification with corrupted content."""
        test_content = "Test content"
        source_url = "https://example.com/test"

        cache_manager.write_content(sample_canonical, test_content, source_url)

        # Corrupt the content
        content_path = cache_manager.get_content_path(sample_canonical)
        content_path.write_text("Corrupted content")

        # Verify checksum should fail
        assert cache_manager.verify_checksum(sample_canonical) is False

    def test_list_cached_empty(self, cache_manager: CacheManager) -> None:
        """Test listing cached files when empty."""
        cached = cache_manager.list_cached()
        assert len(cached) == 0

    def test_list_cached_with_content(
        self, cache_manager: CacheManager, sample_canonical: CanonicalID
    ) -> None:
        """Test listing cached files with content."""
        cache_manager.write_content(sample_canonical, "Content", "https://example.com")

        cached = cache_manager.list_cached()
        assert len(cached) == 1
        assert cached[0].name == "ohs-2004.txt"

    def test_list_cached_by_jurisdiction(self, cache_manager: CacheManager) -> None:
        """Test listing cached files filtered by jurisdiction."""
        # Write Victorian legislation
        vic_canonical = CanonicalID("au-victoria", "ohs", "2004")
        cache_manager.write_content(vic_canonical, "VIC", "https://example.com")

        # Write Federal legislation
        fed_canonical = CanonicalID("au-federal", "fwa", "2009")
        cache_manager.write_content(fed_canonical, "FED", "https://example.com")

        # List all
        all_cached = cache_manager.list_cached()
        assert len(all_cached) == 2

        # List Victorian only
        vic_cached = cache_manager.list_cached(jurisdiction="au-victoria")
        assert len(vic_cached) == 1
        assert "au-victoria" in str(vic_cached[0])

    def test_get_cache_size(
        self, cache_manager: CacheManager, sample_canonical: CanonicalID
    ) -> None:
        """Test getting total cache size."""
        # Empty cache
        assert cache_manager.get_cache_size() == 0

        # Add content
        test_content = "Test content with some length"
        cache_manager.write_content(sample_canonical, test_content, "https://example.com")

        # Check size
        size = cache_manager.get_cache_size()
        assert size > 0
        assert size == len(test_content.encode("utf-8"))


class TestLegislationMetadata:
    """Test legislation metadata."""

    def test_from_dict(self) -> None:
        """Test creating metadata from dictionary."""
        data = {
            "canonical_id": "/au-victoria/ohs/2004",
            "source_url": "https://example.com",
            "fetch_timestamp": "2024-01-01T00:00:00",
            "content_hash": "abc123",
            "file_size": 1000,
            "jurisdiction": "au-victoria",
            "code_type": "ohs",
            "year": "2004",
        }

        metadata = LegislationMetadata.from_dict(data)
        assert metadata.canonical_id == "/au-victoria/ohs/2004"
        assert metadata.source_url == "https://example.com"

    def test_to_dict(self) -> None:
        """Test converting metadata to dictionary."""
        metadata = LegislationMetadata(
            canonical_id="/au-victoria/ohs/2004",
            source_url="https://example.com",
            fetch_timestamp="2024-01-01T00:00:00",
            content_hash="abc123",
            file_size=1000,
            jurisdiction="au-victoria",
            code_type="ohs",
            year="2004",
        )

        data = metadata.to_dict()
        assert data["canonical_id"] == "/au-victoria/ohs/2004"
        assert data["source_url"] == "https://example.com"
        assert isinstance(data, dict)
