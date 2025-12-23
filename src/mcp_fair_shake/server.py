"""MCP Fair Shake Server - Australian Workplace Legislation Lookup.

Provides authoritative access to Australian workplace legislation through:
- resolve-legislation: Find legislation by natural language or citation
- get-legislation-content: Retrieve full legislation text
- get-cache-status: Check cache coverage and status
"""

import json
import logging
from typing import Literal

from fastmcp import FastMCP

from .cache import CacheManager
from .canonical_id import parse_canonical_id
from .fetcher import LEGISLATION_SOURCES, LegislationFetcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("mcp-fair-shake")

# Initialize cache manager and fetcher
cache_manager = CacheManager()
fetcher = LegislationFetcher(cache_manager=cache_manager)


@mcp.tool()
def resolve_legislation(
    query: str,
    jurisdiction: str | None = None,
) -> str:
    """Resolve natural language query or citation to canonical legislation ID.

    Handles fuzzy matching and returns ranked results.

    Args:
        query: Natural language query or citation (e.g., "unfair dismissal",
               "OHS Act s.21", "Fair Work Act section 394")
        jurisdiction: Optional jurisdiction filter (e.g., "au-victoria", "au-federal")

    Returns:
        JSON string with ranked legislation matches

    Example:
        >>> resolve_legislation("unfair dismissal")
        '{"matches": [{"id": "/au-federal/fwa/2009", "title": "Fair Work Act 2009", ...}]}'
    """
    if not query:
        return json.dumps({"error": "Query is required"})

    query_lower = query.lower()
    matches = []

    # Search through available legislation sources
    for canonical_id, info in LEGISLATION_SOURCES.items():
        # Filter by jurisdiction if specified
        if jurisdiction:
            if not canonical_id.startswith(f"/{jurisdiction}/"):
                continue

        # Simple matching logic (can be enhanced)
        title_lower = info["title"].lower()
        score = 0

        # Exact title match
        if query_lower == title_lower:
            score = 100
        # Title contains query
        elif query_lower in title_lower:
            score = 80
        # Query contains key terms
        elif any(
            term in query_lower
            for term in ["unfair dismissal", "fair work", "ohs", "equal opportunity"]
        ):
            if "unfair dismissal" in query_lower and "fair work" in title_lower:
                score = 90
            elif "ohs" in query_lower and "occupational health" in title_lower:
                score = 90
            elif "equal opportunity" in query_lower and "equal opportunity" in title_lower:
                score = 90

        # Parse canonical ID for structured info
        canonical = parse_canonical_id(canonical_id)
        if canonical and score > 0:
            matches.append(
                {
                    "id": canonical_id,
                    "title": info["title"],
                    "jurisdiction": canonical.jurisdiction,
                    "code_type": canonical.code_type,
                    "year": canonical.year,
                    "score": score,
                    "cached": fetcher.is_cached(canonical_id),
                    "source_url": info["url"],
                }
            )

    # Sort by score (highest first)
    from typing import cast

    matches.sort(key=lambda x: cast(int, x["score"]), reverse=True)

    return json.dumps(
        {
            "query": query,
            "jurisdiction_filter": jurisdiction,
            "matches": matches,
            "total": len(matches),
        },
        indent=2,
    )


@mcp.tool()
def get_legislation_content(
    canonical_id: str,
    mode: Literal["text", "summary", "metadata"] = "text",
    section: str | None = None,
) -> str:
    """Retrieve legislation content from cache or download if needed.

    Args:
        canonical_id: Canonical legislation ID (e.g., "/au-victoria/ohs/2004")
        mode: Content mode - "text" (full statutory text), "summary" (plain language),
              or "metadata" (dates, amendments, related provisions)
        section: Optional section filter (e.g., "s21")

    Returns:
        Legislation content as text or JSON error

    Example:
        >>> get_legislation_content("/au-victoria/ohs/2004", mode="text")
        "# Occupational Health and Safety Act 2004\\n\\n..."
    """
    if not canonical_id:
        return json.dumps({"error": "canonical_id is required"})

    # Validate canonical ID
    canonical = parse_canonical_id(canonical_id)
    if canonical is None:
        return json.dumps({"error": f"Invalid canonical ID: {canonical_id}"})

    try:
        # Handle different modes
        if mode == "metadata":
            # Return metadata only
            metadata = cache_manager.read_metadata(canonical)
            if not metadata:
                return json.dumps(
                    {"error": f"No metadata found for {canonical_id}"}
                )

            return json.dumps(
                {
                    "canonical_id": canonical_id,
                    "mode": mode,
                    "metadata": metadata.to_dict(),
                },
                indent=2,
            )

        elif mode == "summary":
            # Return plain language summary
            from .summaries import get_summary

            summary = get_summary(canonical_id, section)
            if not summary:
                return json.dumps(
                    {
                        "error": f"No summary available for {canonical_id}",
                        "suggestion": "Use mode='text' to get the full statutory text",
                    }
                )

            return json.dumps(
                {
                    "canonical_id": canonical_id,
                    "mode": mode,
                    "section": section,
                    "summary": summary,
                },
                indent=2,
            )

        else:  # mode == "text"
            # Fetch full text content (checks cache first)
            content = fetcher.fetch(canonical_id)

            # Filter by section if requested
            if section:
                # Simple section filtering (can be enhanced with proper parsing)
                lines = content.split("\n")
                section_content = []
                in_section = False

                for line in lines:
                    # Simple pattern matching for sections
                    if (
                        f"section {section}" in line.lower()
                        or f"s.{section}" in line.lower()
                        or f"s {section}" in line.lower()
                    ):
                        in_section = True
                    elif in_section and line.strip() and line[0].isdigit():
                        # Stop at next numbered section
                        break

                    if in_section:
                        section_content.append(line)

                if section_content:
                    content = "\n".join(section_content)
                else:
                    content = f"[Section {section} not found in content]\n\n{content[:1000]}..."

            # Get metadata
            metadata = cache_manager.read_metadata(canonical)

            return json.dumps(
                {
                    "canonical_id": canonical_id,
                    "mode": mode,
                    "section": section,
                    "content": content,
                    "metadata": metadata.to_dict() if metadata else None,
                },
                indent=2,
            )

    except Exception as e:
        logger.error(f"Error fetching legislation {canonical_id}: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_cache_status() -> str:
    """Get cache status including coverage, size, and missing items.

    Returns:
        JSON string with cache statistics

    Example:
        >>> get_cache_status()
        '{"total_cached": 3, "cache_size_mb": 3.2, ...}'
    """
    try:
        # Count cached items by priority
        p0_sources = {
            "/au-federal/fwa/2009",
            "/au-victoria/ohs/2004",
            "/au-victoria/eoa/2010",
        }

        cached_p0 = []
        missing_p0 = []

        for canonical_id in p0_sources:
            if fetcher.is_cached(canonical_id):
                cached_p0.append(canonical_id)
            else:
                missing_p0.append(canonical_id)

        # Get total cache info
        total_cached = len(cache_manager.list_cached())
        cache_size_bytes = cache_manager.get_cache_size()
        cache_size_mb = cache_size_bytes / (1024 * 1024)

        # Get metadata for cached items
        cached_items = []
        for path in cache_manager.list_cached():
            # Extract info from path
            parts = path.parts
            jurisdiction = parts[-2]  # e.g., "au-victoria"
            filename = parts[-1]  # e.g., "ohs-2004.txt"

            cached_items.append(
                {
                    "path": str(path),
                    "jurisdiction": jurisdiction,
                    "filename": filename,
                    "size_kb": path.stat().st_size / 1024,
                }
            )

        return json.dumps(
            {
                "total_cached": total_cached,
                "cache_size_mb": round(cache_size_mb, 2),
                "cache_size_bytes": cache_size_bytes,
                "p0_coverage": {
                    "total": len(p0_sources),
                    "cached": len(cached_p0),
                    "missing": len(missing_p0),
                    "percentage": round(len(cached_p0) / len(p0_sources) * 100, 1),
                },
                "cached_p0": cached_p0,
                "missing_p0": missing_p0,
                "cached_items": cached_items,
                "supported_legislation": list(LEGISLATION_SOURCES.keys()),
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        return json.dumps({"error": str(e)})


def main() -> None:
    """Run the MCP server."""
    logger.info("Starting MCP Fair Shake server...")
    mcp.run()


if __name__ == "__main__":
    main()
