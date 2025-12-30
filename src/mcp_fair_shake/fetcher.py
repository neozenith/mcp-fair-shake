"""Legislation fetcher for downloading from official sources."""

import asyncio
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
        "url": "https://www.legislation.gov.au/F2009L02356/latest/text",
        "title": "Fair Work Regulations 2009",
    },
    # Modern Awards (Fair Work Commission)
    # Top 10 most common Modern Awards by employee coverage
    "/au-federal/ma/000004": {
        "url": "https://www.fwc.gov.au/documents/modern_awards/pdf/ma000004.pdf",
        "title": "General Retail Industry Award 2020",
        "format": "pdf",
        "page_url": "https://awards.fairwork.gov.au/MA000004.html",
    },
    "/au-federal/ma/000003": {
        "url": "https://www.fwc.gov.au/documents/modern_awards/pdf/ma000003.pdf",
        "title": "Fast Food Industry Award 2010",
        "format": "pdf",
        "page_url": "https://awards.fairwork.gov.au/MA000003.html",
    },
    "/au-federal/ma/000009": {
        "url": "https://www.fwc.gov.au/documents/modern_awards/pdf/ma000009.pdf",
        "title": "Hospitality Industry (General) Award 2020",
        "format": "pdf",
        "page_url": "https://awards.fairwork.gov.au/MA000009.html",
    },
    "/au-federal/ma/000018": {
        "url": "https://www.fwc.gov.au/documents/modern_awards/pdf/ma000018.pdf",
        "title": "Aged Care Award 2010",
        "format": "pdf",
        "page_url": "https://awards.fairwork.gov.au/MA000018.html",
    },
    "/au-federal/ma/000022": {
        "url": "https://www.fwc.gov.au/documents/modern_awards/pdf/ma000022.pdf",
        "title": "Cleaning Services Award 2020",
        "format": "pdf",
        "page_url": "https://awards.fairwork.gov.au/MA000022.html",
    },
    "/au-federal/ma/000005": {
        "url": "https://www.fwc.gov.au/documents/modern_awards/pdf/ma000005.pdf",
        "title": "Hair and Beauty Industry Award 2010",
        "format": "pdf",
        "page_url": "https://awards.fairwork.gov.au/MA000005.html",
    },
    "/au-federal/ma/000034": {
        "url": "https://www.fwc.gov.au/documents/modern_awards/pdf/ma000034.pdf",
        "title": "Nurses Award 2020",
        "format": "pdf",
        "page_url": "https://awards.fairwork.gov.au/MA000034.html",
    },
    "/au-federal/ma/000120": {
        "url": "https://www.fwc.gov.au/documents/modern_awards/pdf/ma000120.pdf",
        "title": "Children's Services Award 2020",
        "format": "pdf",
        "page_url": "https://awards.fairwork.gov.au/MA000120.html",
    },
    "/au-federal/ma/000106": {
        "url": "https://www.fwc.gov.au/documents/modern_awards/pdf/ma000106.pdf",
        "title": "Real Estate Industry Award 2020",
        "format": "pdf",
        "page_url": "https://awards.fairwork.gov.au/MA000106.html",
    },
    "/au-federal/ma/000002": {
        "url": "https://www.fwc.gov.au/documents/modern_awards/pdf/ma000002.pdf",
        "title": "Clerks - Private Sector Award 2020",
        "format": "pdf",
        "page_url": "https://awards.fairwork.gov.au/MA000002.html",
    },
    # Victorian sources (legislation.vic.gov.au)
    # NOTE: Victorian legislation only available as PDF downloads
    "/au-victoria/ohs/2004": {
        "url": "https://content.legislation.vic.gov.au/sites/default/files/2025-08/04-107aa045-authorised.PDF",
        "title": "Occupational Health and Safety Act 2004",
        "format": "pdf",
        "page_url": "https://www.legislation.vic.gov.au/in-force/acts/occupational-health-and-safety-act-2004/045",
    },
    "/au-victoria/eoa/2010": {
        "url": "https://content.legislation.vic.gov.au/sites/default/files/2025-09/10-16aa031-authorised.pdf",
        "title": "Equal Opportunity Act 2010",
        "format": "pdf",
        "page_url": "https://www.legislation.vic.gov.au/in-force/acts/equal-opportunity-act-2010",
    },
    "/au-victoria/lsl/2018": {
        "url": "https://content.legislation.vic.gov.au/sites/default/files/2025-12/18-12aa006-authorised.pdf",
        "title": "Long Service Leave Act 2018",
        "format": "pdf",
        "page_url": "https://www.legislation.vic.gov.au/in-force/acts/long-service-leave-act-2018",
    },
    "/au-victoria/wca/1958": {
        "url": "https://content.legislation.vic.gov.au/sites/default/files/2023-09/58-6419aa161-authorised.pdf",
        "title": "Workers Compensation Act 1958",
        "format": "pdf",
        "page_url": "https://www.legislation.vic.gov.au/in-force/acts/workers-compensation-act-1958",
    },
    "/au-victoria/aca/1985": {
        "url": "https://content.legislation.vic.gov.au/sites/default/files/2025-10/85-10191aa235-authorised.pdf",
        "title": "Accident Compensation Act 1985",
        "format": "pdf",
        "page_url": "https://www.legislation.vic.gov.au/in-force/acts/accident-compensation-act-1985",
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

        # Check if source is PDF format
        is_pdf = source_info.get("format") == "pdf" or source_info["url"].lower().endswith(".pdf")

        if is_pdf:
            # Download and parse PDF (sync version)
            pdf_bytes = self._download_pdf_sync(source_info["url"])
            content, document_info = self._parse_pdf_content(
                pdf_bytes, source_info["title"], source_url=source_info["url"]
            )

            # Cache with PDF metadata
            self.cache_manager.write_content(
                base_canonical,
                content,
                source_url=source_info["url"],
                title=source_info["title"],
                document_info=document_info,
            )

            return content

        # Download HTML legislation
        content = self._download_with_retry(source_info["url"], source_info["title"], base_id)

        # Cache the content
        self.cache_manager.write_content(
            base_canonical,
            content,
            source_url=source_info["url"],
            title=source_info["title"],
        )

        return content

    async def fetch_async(
        self, canonical_id: str, use_playwright: bool | None = None, force: bool = False
    ) -> str:
        """Fetch legislation content asynchronously.

        Supports Playwright for JavaScript-rendered sites (Victorian legislation).
        Falls back to httpx for static sites (federal legislation).

        Args:
            canonical_id: Canonical ID string (e.g., /au-victoria/ohs/2004)
            use_playwright: Force Playwright rendering (True), force httpx (False),
                          or auto-detect (None). Auto-detection uses Playwright
                          for Victorian sites.
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

        # Check if source is PDF format
        is_pdf = source_info.get("format") == "pdf" or source_info["url"].lower().endswith(".pdf")

        # Download legislation (PDF or HTML)
        if is_pdf:
            # Download and parse PDF
            pdf_bytes = await self._download_pdf(source_info["url"])
            content, document_info = self._parse_pdf_content(
                pdf_bytes, source_info["title"], source_url=source_info["url"]
            )

            # Cache with PDF metadata
            self.cache_manager.write_content(
                base_canonical,
                content,
                source_url=source_info["url"],
                title=source_info["title"],
                document_info=document_info,
            )

            return content

        # Auto-detect Playwright need if not specified for HTML sources
        if use_playwright is None:
            use_playwright = self._should_use_playwright(canonical.jurisdiction)

        # Download HTML legislation (Playwright or httpx)
        if use_playwright:
            content = await self._download_with_playwright(
                source_info["url"], source_info["title"], base_id
            )
        else:
            # Use sync httpx in async context
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None, self._download_with_retry, source_info["url"], source_info["title"], base_id
            )

        # Cache the content
        self.cache_manager.write_content(
            base_canonical,
            content,
            source_url=source_info["url"],
            title=source_info["title"],
        )

        return content

    def _should_use_playwright(self, jurisdiction: str) -> bool:
        """Determine if Playwright is needed for this jurisdiction.

        Victorian legislation sites (legislation.vic.gov.au) use JavaScript
        rendering and require Playwright. Federal sites work with httpx.

        Args:
            jurisdiction: Jurisdiction code (e.g., 'au-victoria', 'au-federal')

        Returns:
            True if Playwright should be used, False otherwise
        """
        # Victorian sites need Playwright
        if "victoria" in jurisdiction.lower():
            return True

        # Federal sites work with httpx
        return False

    async def _download_with_playwright(self, url: str, title: str, canonical_id: str) -> str:
        """Download legislation using Playwright for JavaScript rendering.

        Args:
            url: URL to download from
            title: Title of the legislation
            canonical_id: Canonical ID for error messages

        Returns:
            Downloaded content

        Raises:
            LegislationFetchError: If download fails
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise LegislationFetchError(
                "Playwright is required for Victorian legislation. "
                "Install with: uv add playwright && uv run playwright install chromium"
            ) from None

        try:
            async with async_playwright() as p:
                # Launch browser (headless mode)
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Set user agent
                await page.set_extra_http_headers(
                    {"User-Agent": "MCP-Fair-Shake/1.0 (Legislation Research Tool)"}
                )

                # Navigate to page and wait for JavaScript rendering
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Get rendered HTML
                html = await page.content()

                # Close browser
                await browser.close()

                # Parse HTML to extract legislation text
                content = self._parse_html_content(html, title)

                if not content.strip():
                    raise LegislationFetchError(f"Empty content received for {canonical_id}")

                return content

        except Exception as e:
            raise LegislationFetchError(
                f"Playwright error fetching {canonical_id} from {url}: {e}"
            ) from e

    def _download_pdf_sync(self, url: str) -> bytes:
        """Download PDF file from URL (synchronous version).

        Args:
            url: URL to download PDF from

        Returns:
            PDF content as bytes

        Raises:
            LegislationFetchError: If download fails or not a valid PDF
        """
        try:
            response = self.client.get(url)
            response.raise_for_status()

            pdf_bytes = response.content

            # Verify it's a valid PDF
            if not pdf_bytes.startswith(b"%PDF-"):
                raise LegislationFetchError(f"Downloaded file from {url} is not a valid PDF")

            return pdf_bytes

        except httpx.HTTPStatusError as e:
            raise LegislationFetchError(
                f"HTTP error {e.response.status_code} downloading PDF from {url}: {e}"
            ) from e
        except httpx.RequestError as e:
            raise LegislationFetchError(f"Network error downloading PDF from {url}: {e}") from e
        except Exception as e:
            raise LegislationFetchError(f"Unexpected error downloading PDF from {url}: {e}") from e

    async def _download_pdf(self, url: str) -> bytes:
        """Download PDF file from URL.

        Args:
            url: URL to download PDF from

        Returns:
            PDF content as bytes

        Raises:
            LegislationFetchError: If download fails or not a valid PDF
        """
        try:
            # Use async httpx for PDF download
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                pdf_bytes = response.content

                # Verify it's a valid PDF
                if not pdf_bytes.startswith(b"%PDF-"):
                    raise LegislationFetchError(f"Downloaded file from {url} is not a valid PDF")

                return pdf_bytes

        except httpx.HTTPStatusError as e:
            raise LegislationFetchError(
                f"HTTP error {e.response.status_code} downloading PDF from {url}: {e}"
            ) from e
        except httpx.RequestError as e:
            raise LegislationFetchError(f"Network error downloading PDF from {url}: {e}") from e
        except Exception as e:
            raise LegislationFetchError(f"Unexpected error downloading PDF from {url}: {e}") from e

    def _parse_pdf_content(
        self, pdf_bytes: bytes, title: str, source_url: str
    ) -> tuple[str, dict[str, str]]:
        """Parse PDF to extract legislation text with page number audit trail.

        CRITICAL: Preserves page numbers for accurate legal citations.
        Each page is marked with [Page N] for traceable references.

        Args:
            pdf_bytes: PDF file content as bytes
            title: Title of the legislation
            source_url: URL where PDF was downloaded from (for audit trail)

        Returns:
            Tuple of (extracted_text, document_info)
            - extracted_text: Legislation text with page markers
            - document_info: PDF metadata (title, author, creation_date, etc.)

        Raises:
            LegislationFetchError: If PDF parsing fails
        """
        try:
            from io import BytesIO

            from pypdf import PdfReader
        except ImportError:
            raise LegislationFetchError(
                "pypdf is required for PDF parsing. Install with: uv add pypdf"
            ) from None

        try:
            # Parse PDF
            pdf_file = BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)

            # Extract metadata for audit trail
            metadata = reader.metadata
            document_info = {
                "source_url": source_url,
                "page_count": str(len(reader.pages)),
            }

            if metadata:
                # Add available metadata fields
                if metadata.title:
                    document_info["title"] = metadata.title
                if metadata.author:
                    document_info["author"] = metadata.author
                if metadata.creator:
                    document_info["creator"] = metadata.creator
                if metadata.producer:
                    document_info["producer"] = metadata.producer
                if metadata.creation_date:
                    document_info["creation_date"] = str(metadata.creation_date)
                if metadata.modification_date:
                    document_info["modification_date"] = str(metadata.modification_date)

            # Extract text with page markers
            lines = [f"# {title}\n"]
            lines.append(f"\n**Source**: {source_url}\n")
            lines.append(f"**Pages**: {len(reader.pages)}\n")

            if document_info.get("creation_date"):
                lines.append(f"**Created**: {document_info['creation_date']}\n")

            lines.append("\n---\n\n")

            # Extract text from each page with page markers
            for page_num, page in enumerate(reader.pages, start=1):
                # Add page marker for citation tracking
                lines.append(f"\n[Page {page_num}]\n\n")

                # Extract text from page
                page_text = page.extract_text()

                if page_text:
                    # Clean up text (remove excessive whitespace)
                    page_text = page_text.strip()

                    # Add page content
                    lines.append(page_text)
                    lines.append("\n")

            # Join all content
            content = "".join(lines)

            # Clean up excessive newlines (but preserve page markers)
            while "\n\n\n\n" in content:
                content = content.replace("\n\n\n\n", "\n\n\n")

            return content, document_info

        except Exception as e:
            raise LegislationFetchError(f"Error parsing PDF: {e}") from e

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

        Handles legislation.gov.au EPUB content with proper structure preservation.
        Detects TOC pages with iframes and downloads the actual EPUB content.

        Args:
            html: HTML content
            title: Title of the legislation

        Returns:
            Extracted text content with hierarchical structure preserved
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return (
                f"# {title}\n\n[ERROR: BeautifulSoup not installed. Run: uv add beautifulsoup4]\n"
            )

        if not html or not html.strip():
            return f"# {title}\n\n[No content found in HTML]\n"

        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # Check if this is a legislation.gov.au TOC page with iframe
        iframe = soup.find("iframe")
        if iframe and iframe.get("src") and "epub/OEBPS" in iframe["src"]:
            # This is a TOC page - download the actual EPUB content
            epub_url = iframe["src"]

            # Make URL absolute if needed
            if not epub_url.startswith("http"):
                base_url = "https://www.legislation.gov.au"
                epub_url = base_url + epub_url if epub_url.startswith("/") else base_url + "/" + epub_url

            # Download EPUB content
            try:
                response = self.client.get(epub_url)
                response.raise_for_status()
                html = response.text
                soup = BeautifulSoup(html, "html.parser")
            except Exception as e:
                return f"# {title}\n\n[ERROR: Failed to download EPUB content: {e}]\n"

        # Remove script and style elements
        for element in soup(["script", "style", "noscript"]):
            element.decompose()

        # Check if this is EPUB content (has ActHead classes)
        has_epub_classes = soup.find("p", class_=lambda c: c and any(
            cls in c for cls in ["ActHead2", "ActHead3", "ActHead5", "subsection", "paragraph"]
        ))

        if has_epub_classes:
            # Parse EPUB structure with class-based hierarchy
            return self._parse_epub_structure(soup, title)
        else:
            # Fallback to generic HTML parsing
            return self._parse_generic_html(soup, title)

    def _parse_epub_structure(self, soup, title: str) -> str:
        """Parse legislation.gov.au EPUB structure.

        Maps EPUB paragraph classes to legislation hierarchy:
        - ActHead2 = Part (e.g., "Part 1-1—Introduction")
        - ActHead3 = Division (e.g., "Division 1—Preliminary")
        - ActHead5 = Section (e.g., "1  Short title")
        - subsection class = Subsection content with (1), (2) markers
        - paragraph class = Paragraph content with (a), (b) markers
        """
        import re

        lines = [f"# {title}\n"]

        # Find all paragraph elements
        paragraphs = soup.find_all("p")

        for p in paragraphs:
            classes = p.get("class", [])
            text = p.get_text(strip=True)

            if not text or len(text) < 2:
                continue

            # Part headings (ActHead2)
            if "ActHead2" in classes:
                # Extract part number and title from "Part1‑1—Introduction" (NO space in EPUB!)
                if text.startswith("Part"):
                    # Insert space after "Part" to match parser expectations
                    part_text = text.replace("Part", "Part ", 1)
                    lines.append(f"\nCollapse{part_text}")
                    continue

            # Division headings (ActHead3)
            if "ActHead3" in classes:
                # Extract division number and title from "Division1—Preliminary" (NO space in EPUB!)
                if text.startswith("Division"):
                    # Insert space after "Division" to match parser expectations
                    div_text = text.replace("Division", "Division ", 1)
                    lines.append(f"\nCollapse{div_text}")
                    continue

            # Section headings (ActHead5)
            if "ActHead5" in classes:
                # EPUB structure: <p class="ActHead5"><span class="CharSectno">1</span><span>Short title</span></p>
                # Extract section number from CharSectno span
                sectno_span = p.find("span", class_="CharSectno")
                if sectno_span:
                    section_num = sectno_span.get_text(strip=True)
                    # Get title from all other spans (not CharSectno)
                    title_parts = []
                    for span in p.find_all("span"):
                        if "CharSectno" not in span.get("class", []):
                            title_parts.append(span.get_text(strip=True))

                    section_title = "".join(title_parts).strip()

                    if section_title:
                        # Insert double space to match parser expectations
                        lines.append(f"\n{section_num}  {section_title}")
                        continue

            # Subsection content
            if "subsection" in classes or "SubsectionHead" in classes:
                # Preserve subsection markers like "(1)", "(2)", "(2a)"
                lines.append(text)
                continue

            # Paragraph content
            if "paragraph" in classes or "paragraphsub" in classes:
                # Preserve paragraph markers like "(a)", "(b)", "(aa)"
                lines.append(text)
                continue

            # Definition content
            if "Definition" in classes:
                lines.append(text)
                continue

            # Skip metadata classes
            if any(cls in classes for cls in ["TOC1", "TOC2", "TOC3", "TOC4", "TOC5",
                                               "ShortT", "CompiledActNo", "Header",
                                               "notetext", "notepara"]):
                continue

            # Include other substantial paragraph content
            if len(text) > 10:
                lines.append(text)

        # Join with newlines and clean up
        content = "\n".join(lines)

        # Remove excessive newlines (but keep structure)
        while "\n\n\n\n" in content:
            content = content.replace("\n\n\n\n", "\n\n\n")

        return content

    def _parse_generic_html(self, soup, title: str) -> str:
        """Fallback generic HTML parser for non-EPUB content."""
        # Try to find main content areas
        content_selectors = [
            "main",
            'div[class*="content"]',
            'div[class*="act"]',
            'div[class*="legislation"]',
            "article",
            'div[role="main"]',
            "body",
        ]

        content_div = None
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                break

        if not content_div:
            content_div = soup.find("body") or soup

        # Extract text with some structure preservation
        lines = [f"# {title}\n"]

        # Find all headings and paragraphs
        for element in content_div.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "div"]):
            text = element.get_text(strip=True)
            if not text or len(text) < 3:
                continue

            # Format based on element type
            if element.name in ["h1", "h2"]:
                lines.append(f"\n## {text}\n")
            elif element.name in ["h3", "h4"]:
                lines.append(f"\n### {text}\n")
            elif element.name == "p":
                lines.append(f"{text}\n")
            elif element.name == "li":
                lines.append(f"- {text}")
            elif element.name == "div":
                if len(text) > 20 and not element.find(["h1", "h2", "h3", "p", "div"]):
                    lines.append(f"{text}\n")

        # Join and clean up
        content = "\n".join(lines)

        # Remove excessive newlines
        while "\n\n\n" in content:
            content = content.replace("\n\n\n", "\n\n")

        # Ensure we got some content
        if len(content.strip()) < 100:
            all_text = soup.get_text(separator="\n", strip=True)
            content = f"# {title}\n\n{all_text}"

        return content

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
