"""Cache management for Australian legislation."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .canonical_id import CanonicalID

# Cache base directory (relative to project root)
CACHE_BASE = Path(__file__).parent.parent.parent / "data" / "legislation" / "cache"


@dataclass
class LegislationMetadata:
    """Metadata for cached legislation."""

    canonical_id: str
    source_url: str
    fetch_timestamp: str
    content_hash: str
    file_size: int
    jurisdiction: str
    code_type: str
    year: str
    section_count: int | None = None
    title: str | None = None
    document_info: dict[str, str] | None = None  # PDF metadata for audit trail

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LegislationMetadata":
        """Create metadata from dictionary."""
        return cls(**data)

    def to_dict(self) -> dict[str, object]:
        """Convert metadata to dictionary."""
        return asdict(self)


class CacheManager:
    """Manage cached legislation files."""

    def __init__(self, base_dir: Path | None = None):
        """Initialize cache manager.

        Args:
            base_dir: Base directory for cache (defaults to data/legislation/cache)
        """
        self.base_dir = base_dir or CACHE_BASE
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_path(self, canonical: CanonicalID) -> Path:
        """Get the cache directory path for a canonical ID.

        Args:
            canonical: Parsed canonical ID

        Returns:
            Path to the jurisdiction directory
        """
        return self.base_dir / canonical.jurisdiction

    def get_content_path(self, canonical: CanonicalID) -> Path:
        """Get the content file path for a canonical ID.

        Args:
            canonical: Parsed canonical ID

        Returns:
            Path to the content text file
        """
        cache_dir = self.get_cache_path(canonical)
        return cache_dir / canonical.cache_filename

    def get_metadata_path(self, canonical: CanonicalID) -> Path:
        """Get the metadata file path for a canonical ID.

        Args:
            canonical: Parsed canonical ID

        Returns:
            Path to the metadata JSON file
        """
        cache_dir = self.get_cache_path(canonical)
        return cache_dir / canonical.metadata_filename

    def get_checksum_path(self, canonical: CanonicalID) -> Path:
        """Get the checksum file path for a canonical ID.

        Args:
            canonical: Parsed canonical ID

        Returns:
            Path to the checksum file
        """
        cache_dir = self.get_cache_path(canonical)
        return cache_dir / canonical.checksum_filename

    def exists(self, canonical: CanonicalID) -> bool:
        """Check if legislation is cached.

        Args:
            canonical: Parsed canonical ID

        Returns:
            True if content file exists, False otherwise
        """
        return self.get_content_path(canonical).exists()

    def read_content(self, canonical: CanonicalID) -> str | None:
        """Read cached legislation content.

        Args:
            canonical: Parsed canonical ID

        Returns:
            Legislation content as string, or None if not cached
        """
        content_path = self.get_content_path(canonical)
        if not content_path.exists():
            return None

        return content_path.read_text(encoding="utf-8")

    def write_content(
        self,
        canonical: CanonicalID,
        content: str,
        source_url: str,
        title: str | None = None,
        document_info: dict[str, str] | None = None,
    ) -> None:
        """Write legislation content to cache.

        Args:
            canonical: Parsed canonical ID
            content: Legislation content
            source_url: URL where content was fetched from
            title: Optional title of the legislation
            document_info: Optional PDF metadata (for audit trail)
        """
        # Ensure cache directory exists
        cache_dir = self.get_cache_path(canonical)
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Write content
        content_path = self.get_content_path(canonical)
        content_path.write_text(content, encoding="utf-8")

        # Calculate and write checksum
        content_hash = self._calculate_hash(content)
        checksum_path = self.get_checksum_path(canonical)
        checksum_path.write_text(content_hash, encoding="utf-8")

        # Write metadata
        metadata = LegislationMetadata(
            canonical_id=canonical.full_id,
            source_url=source_url,
            fetch_timestamp=datetime.now(UTC).isoformat(),
            content_hash=content_hash,
            file_size=len(content.encode("utf-8")),
            jurisdiction=canonical.jurisdiction,
            code_type=canonical.code_type,
            year=canonical.year,
            title=title,
            document_info=document_info,  # Include PDF metadata for audit trail
        )
        self.write_metadata(canonical, metadata)

    def read_metadata(self, canonical: CanonicalID) -> LegislationMetadata | None:
        """Read cached legislation metadata.

        Args:
            canonical: Parsed canonical ID

        Returns:
            LegislationMetadata object, or None if not cached
        """
        metadata_path = self.get_metadata_path(canonical)
        if not metadata_path.exists():
            return None

        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        return LegislationMetadata.from_dict(data)

    def write_metadata(self, canonical: CanonicalID, metadata: LegislationMetadata) -> None:
        """Write legislation metadata to cache.

        Args:
            canonical: Parsed canonical ID
            metadata: Metadata object
        """
        metadata_path = self.get_metadata_path(canonical)
        metadata_path.write_text(json.dumps(metadata.to_dict(), indent=2), encoding="utf-8")

    def verify_checksum(self, canonical: CanonicalID) -> bool:
        """Verify the checksum of cached content.

        Args:
            canonical: Parsed canonical ID

        Returns:
            True if checksum matches, False otherwise
        """
        content = self.read_content(canonical)
        if content is None:
            return False

        checksum_path = self.get_checksum_path(canonical)
        if not checksum_path.exists():
            return False

        stored_hash = checksum_path.read_text(encoding="utf-8").strip()
        calculated_hash = self._calculate_hash(content)

        return stored_hash == calculated_hash

    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content.

        Args:
            content: Content to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def list_cached(self, jurisdiction: str | None = None) -> list[Path]:
        """List all cached legislation files.

        Args:
            jurisdiction: Optional jurisdiction filter

        Returns:
            List of content file paths
        """
        if jurisdiction:
            pattern = f"{jurisdiction}/*.txt"
        else:
            pattern = "*/*.txt"

        return sorted(self.base_dir.glob(pattern))

    def get_cache_size(self) -> int:
        """Get total size of all cached content in bytes.

        Returns:
            Total size in bytes
        """
        total = 0
        for path in self.list_cached():
            total += path.stat().st_size
        return total
