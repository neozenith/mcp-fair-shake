"""Parquet storage for efficient legislation querying.

Converts cached text files to compressed Parquet format for faster queries
and better storage efficiency.
"""

from pathlib import Path

try:
    import polars as pl
except ImportError:
    pl = None  # type: ignore

from .cache import CacheManager
from .canonical_id import parse_canonical_id

# Parquet base directory
PARQUET_BASE = Path(__file__).parent.parent.parent / "data" / "legislation" / "parquet"


class ParquetStorage:
    """Manage Parquet storage for legislation."""

    def __init__(self, base_dir: Path | None = None):
        """Initialize Parquet storage.

        Args:
            base_dir: Base directory for Parquet files
        """
        if pl is None:
            raise ImportError("polars is required for Parquet storage")

        self.base_dir = base_dir or PARQUET_BASE
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def convert_from_cache(self, canonical_id: str, cache_manager: CacheManager) -> None:
        """Convert cached text file to Parquet format.

        Args:
            canonical_id: Canonical legislation ID
            cache_manager: Cache manager instance
        """
        # Parse canonical ID
        canonical = parse_canonical_id(canonical_id)
        if not canonical:
            raise ValueError(f"Invalid canonical ID: {canonical_id}")

        # Read content and metadata
        content = cache_manager.read_content(canonical)
        if not content:
            raise ValueError(f"No cached content for {canonical_id}")

        metadata = cache_manager.read_metadata(canonical)
        if not metadata:
            raise ValueError(f"No metadata for {canonical_id}")

        # Parse content into sections
        sections = self._parse_sections(content)

        # Create DataFrame
        data = []
        for section_num, section_text in sections.items():
            data.append(
                {
                    "canonical_id": canonical_id,
                    "jurisdiction": canonical.jurisdiction,
                    "code_type": canonical.code_type,
                    "year": canonical.year,
                    "section": section_num,
                    "content": section_text,
                    "title": metadata.title,
                    "source_url": metadata.source_url,
                    "fetch_timestamp": metadata.fetch_timestamp,
                }
            )

        df = pl.DataFrame(data)

        # Write to Parquet
        output_path = self.get_parquet_path(canonical)
        df.write_parquet(output_path, compression="zstd")

    def _parse_sections(self, content: str) -> dict[str, str]:
        """Parse legislation content into sections.

        This is a simple implementation that splits on numbered sections.
        A more sophisticated parser could use proper legislation structure.

        Args:
            content: Legislation text

        Returns:
            Dict mapping section numbers to section text
        """
        sections = {"full": content}

        # Simple pattern matching for sections
        # This is a placeholder - real implementation would use proper parsing
        lines = content.split("\n")
        current_section = None
        section_lines = []

        for line in lines:
            # Look for section headers (e.g., "Section 21", "21.", "s.21")
            if line.strip().startswith(("Section ", "SECTION ")):
                # Save previous section
                if current_section and section_lines:
                    sections[current_section] = "\n".join(section_lines)

                # Start new section
                current_section = line.strip().split()[1].rstrip(".")
                section_lines = [line]
            elif current_section:
                section_lines.append(line)

        # Save last section
        if current_section and section_lines:
            sections[current_section] = "\n".join(section_lines)

        return sections

    def get_parquet_path(self, canonical) -> Path:  # type: ignore
        """Get the Parquet file path for a canonical ID.

        Args:
            canonical: Parsed canonical ID

        Returns:
            Path to Parquet file
        """
        jurisdiction_dir = self.base_dir / canonical.jurisdiction
        jurisdiction_dir.mkdir(parents=True, exist_ok=True)
        return jurisdiction_dir / f"{canonical.code_type}-{canonical.year}.parquet"  # type: ignore[no-any-return]

    def query(
        self,
        canonical_id: str | None = None,
        section: str | None = None,
        jurisdiction: str | None = None,
    ) -> pl.DataFrame | None:
        """Query Parquet storage.

        Args:
            canonical_id: Optional canonical ID filter
            section: Optional section filter
            jurisdiction: Optional jurisdiction filter

        Returns:
            DataFrame with results, or None if no data
        """
        if canonical_id:
            # Query specific legislation
            canonical = parse_canonical_id(canonical_id)
            if not canonical:
                return None

            parquet_path = self.get_parquet_path(canonical)
            if not parquet_path.exists():
                return None

            df = pl.read_parquet(parquet_path)

            # Filter by section if specified
            if section:
                df = df.filter(pl.col("section") == section)

            return df

        elif jurisdiction:
            # Query all legislation in jurisdiction
            jurisdiction_dir = self.base_dir / jurisdiction
            if not jurisdiction_dir.exists():
                return None

            # Read all Parquet files in jurisdiction
            dfs = []
            for parquet_file in jurisdiction_dir.glob("*.parquet"):
                dfs.append(pl.read_parquet(parquet_file))

            if not dfs:
                return None

            return pl.concat(dfs)

        else:
            # Query all legislation
            dfs = []
            for jurisdiction_dir in self.base_dir.iterdir():
                if jurisdiction_dir.is_dir():
                    for parquet_file in jurisdiction_dir.glob("*.parquet"):
                        dfs.append(pl.read_parquet(parquet_file))

            if not dfs:
                return None

            return pl.concat(dfs)

    def get_stats(self) -> dict[str, object]:
        """Get statistics about Parquet storage.

        Returns:
            Dict with storage statistics
        """
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "by_jurisdiction": {},
        }

        for jurisdiction_dir in self.base_dir.iterdir():
            if not jurisdiction_dir.is_dir():
                continue

            jurisdiction = jurisdiction_dir.name
            parquet_files = list(jurisdiction_dir.glob("*.parquet"))

            jurisdiction_size = sum(f.stat().st_size for f in parquet_files)

            stats["total_files"] += len(parquet_files)  # type: ignore[operator]
            stats["total_size_bytes"] += jurisdiction_size  # type: ignore[operator]
            stats["by_jurisdiction"][jurisdiction] = {  # type: ignore[index]
                "files": len(parquet_files),
                "size_bytes": jurisdiction_size,
                "size_mb": round(jurisdiction_size / (1024 * 1024), 2),
            }

        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)  # type: ignore[operator]

        return stats
