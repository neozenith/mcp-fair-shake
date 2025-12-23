"""Legislation fetcher for downloading from official sources."""

import time

try:
    import httpx
except ImportError:
    # httpx will be added as a dependency
    httpx = None  # type: ignore

from .cache import CacheManager
from .canonical_id import parse_canonical_id

# Legislation source URLs
LEGISLATION_SOURCES = {
    # Federal sources (legislation.gov.au)
    "/au-federal/fwa/2009": {
        "url": "https://www.legislation.gov.au/C2009A00028/latest/text",
        "title": "Fair Work Act 2009",
    },
    "/au-federal/fwr/2009": {
        "url": "https://www.legislation.gov.au/F2009L03817/latest/text",
        "title": "Fair Work Regulations 2009",
    },
    # Victorian sources (legislation.vic.gov.au)
    "/au-victoria/ohs/2004": {
        "url": "https://www.legislation.vic.gov.au/as-made/acts/occupational-health-and-safety-act-2004",
        "title": "Occupational Health and Safety Act 2004",
    },
    "/au-victoria/eoa/2010": {
        "url": "https://www.legislation.vic.gov.au/as-made/acts/equal-opportunity-act-2010",
        "title": "Equal Opportunity Act 2010",
    },
}


class LegislationFetchError(Exception):
    """Error fetching legislation."""

    pass


class LegislationFetcher:
    """Fetch legislation from official government websites."""

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize legislation fetcher.

        Args:
            cache_manager: Cache manager instance (creates one if not provided)
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        if httpx is None:
            raise ImportError(
                "httpx is required for fetching legislation. Install with: uv add httpx"
            )

        self.cache_manager = cache_manager or CacheManager()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "MCP-Fair-Shake/1.0 (Legislation Research Tool)",
            },
        )

    def fetch(self, canonical_id: str, force: bool = False) -> str:
        """Fetch legislation content.

        Checks cache first, then downloads if needed.

        Args:
            canonical_id: Canonical ID string (e.g., /au-victoria/ohs/2004)
            force: Force download even if cached

        Returns:
            Legislation content as string

        Raises:
            LegislationFetchError: If fetch fails
            ValueError: If canonical ID is invalid
        """
        # Parse canonical ID (remove section if present)
        canonical = parse_canonical_id(canonical_id)
        if canonical is None:
            raise ValueError(f"Invalid canonical ID: {canonical_id}")

        # Build base ID (without section)
        base_id = f"/{canonical.jurisdiction}/{canonical.code_type}/{canonical.year}"
        base_canonical = parse_canonical_id(base_id)
        if base_canonical is None:
            raise ValueError(f"Invalid base canonical ID: {base_id}")

        # Check cache first
        if not force and self.cache_manager.exists(base_canonical):
            # Verify checksum
            if self.cache_manager.verify_checksum(base_canonical):
                content = self.cache_manager.read_content(base_canonical)
                if content:
                    return content
            else:
                # Checksum mismatch - re-download
                pass

        # Get source URL
        source_info = LEGISLATION_SOURCES.get(base_id)
        if source_info is None:
            raise LegislationFetchError(
                f"No source URL configured for {base_id}. This legislation is not yet supported."
            )

        # Download legislation
        content = self._download_with_retry(source_info["url"], source_info["title"], base_id)

        # Cache the content
        self.cache_manager.write_content(
            base_canonical,
            content,
            source_url=source_info["url"],
            title=source_info["title"],
        )

        return content

    def _download_with_retry(self, url: str, title: str, canonical_id: str) -> str:
        """Download legislation with retry logic.

        Args:
            url: URL to download from
            title: Title of the legislation
            canonical_id: Canonical ID for error messages

        Returns:
            Downloaded content

        Raises:
            LegislationFetchError: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.get(url)
                response.raise_for_status()

                # Check if we got HTML or text
                content_type = response.headers.get("content-type", "")
                if "html" in content_type.lower():
                    # Parse HTML to extract legislation text
                    content = self._parse_html_content(response.text, title)
                else:
                    content = response.text

                if not content.strip():
                    raise LegislationFetchError(f"Empty content received for {canonical_id}")

                return content

            except httpx.HTTPStatusError as e:
                last_error = LegislationFetchError(
                    f"HTTP error {e.response.status_code} fetching {canonical_id} from {url}: {e}"
                )
            except httpx.RequestError as e:
                last_error = LegislationFetchError(
                    f"Network error fetching {canonical_id} from {url}: {e}"
                )
            except Exception as e:
                last_error = LegislationFetchError(f"Unexpected error fetching {canonical_id}: {e}")

            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))

        # All retries failed
        raise last_error or LegislationFetchError(
            f"Failed to fetch {canonical_id} after {self.max_retries} attempts"
        )

    def _parse_html_content(self, html: str, title: str) -> str:
        """Parse HTML to extract legislation text.

        This is a simple implementation that extracts text content.
        A more sophisticated parser could preserve structure, sections, etc.

        Args:
            html: HTML content
            title: Title of the legislation

        Returns:
            Extracted text content
        """
        # For now, return a placeholder
        # In a real implementation, we'd use BeautifulSoup or similar
        # to extract the actual legislation text from the HTML
        return (
            f"# {title}\n\n"
            "[PLACEHOLDER: HTML parsing not yet implemented]\n\n"
            f"Source HTML length: {len(html)} characters\n\n"
            "To implement: Use BeautifulSoup to extract legislation sections "
            "from the HTML structure."
        )

    def is_cached(self, canonical_id: str) -> bool:
        """Check if legislation is cached.

        Args:
            canonical_id: Canonical ID string

        Returns:
            True if cached and checksum valid, False otherwise
        """
        canonical = parse_canonical_id(canonical_id)
        if canonical is None:
            return False

        # Build base ID (without section)
        base_id = f"/{canonical.jurisdiction}/{canonical.code_type}/{canonical.year}"
        base_canonical = parse_canonical_id(base_id)
        if base_canonical is None:
            return False

        return self.cache_manager.exists(base_canonical) and self.cache_manager.verify_checksum(
            base_canonical
        )

    def get_source_info(self, canonical_id: str) -> dict[str, str] | None:
        """Get source information for a canonical ID.

        Args:
            canonical_id: Canonical ID string

        Returns:
            Dict with 'url' and 'title', or None if not configured
        """
        canonical = parse_canonical_id(canonical_id)
        if canonical is None:
            return None

        base_id = f"/{canonical.jurisdiction}/{canonical.code_type}/{canonical.year}"
        return LEGISLATION_SOURCES.get(base_id)

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> "LegislationFetcher":
        """Context manager entry."""
        return self

    def __exit__(self, *args) -> None:  # type: ignore
        """Context manager exit."""
        self.close()
