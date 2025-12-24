"""Tests for PDF parsing with audit trail - TDD approach.

These tests define what the PDF parser MUST do before it can be considered working.
Tests written FIRST, then implementation.

CRITICAL: Audit trail must preserve source URL, page numbers, and document metadata
for accurate legal citations.
"""

import pytest

from mcp_fair_shake.fetcher import LegislationFetcher


class TestPdfParsing:
    """Test PDF parsing extracts legislation with full audit trail."""

    @pytest.mark.asyncio
    async def test_pdf_parser_extracts_real_legislation_content(self) -> None:
        """Test that PDF parser extracts actual legislation text.

        Victorian legislation is only available as PDF. This test will FAIL
        until PDF parsing is implemented.
        """
        fetcher = LegislationFetcher()

        # Fetch Victorian OHS Act (PDF only)
        content = await fetcher.fetch_async("/au-victoria/ohs/2004", force=True)

        # Must have substantial content (OHS Act is long)
        assert len(content) > 50000, f"Content too short: {len(content)} bytes"

        # Must contain actual legislation sections
        assert "section" in content.lower() or "part" in content.lower()

        # Must contain key provisions (Section 21 - employer duties)
        assert "21" in content or "employer" in content.lower()

        fetcher.close()

    @pytest.mark.asyncio
    async def test_pdf_parser_preserves_page_numbers_in_output(self) -> None:
        """Test that extracted content includes page number markers.

        CRITICAL: Legal citations require page numbers for accuracy.
        """
        fetcher = LegislationFetcher()

        content = await fetcher.fetch_async("/au-victoria/ohs/2004", force=True)

        # Must include page markers in extracted text
        # Format: [Page N] or similar marker
        assert "[Page" in content or "Page " in content

        fetcher.close()

    @pytest.mark.asyncio
    async def test_pdf_metadata_includes_source_information(self) -> None:
        """Test that PDF metadata is captured and stored.

        CRITICAL: Audit trail must include:
        - Source URL (where PDF was downloaded from)
        - PDF document info (title, author, creation date)
        - File checksum (verify integrity)
        """
        fetcher = LegislationFetcher()

        # Fetch and ensure metadata is cached
        await fetcher.fetch_async("/au-victoria/ohs/2004", force=True)

        # Check that metadata file exists and has required fields
        from mcp_fair_shake.canonical_id import parse_canonical_id

        canonical = parse_canonical_id("/au-victoria/ohs/2004")
        assert canonical is not None

        metadata = fetcher.cache_manager.read_metadata(canonical)
        assert metadata is not None

        # Must have source URL
        assert metadata.source_url
        assert metadata.source_url.endswith(".PDF") or ".pdf" in metadata.source_url

        # Must have document info
        assert metadata.document_info is not None
        doc_info = metadata.document_info

        # PDF should have at least title or creation date or page count
        assert (
            "title" in doc_info
            or "creation_date" in doc_info
            or "creator" in doc_info
            or "page_count" in doc_info
        )

        fetcher.close()

    @pytest.mark.asyncio
    async def test_pdf_parser_handles_multi_page_documents(self) -> None:
        """Test that multi-page PDFs are fully extracted.

        Victorian Acts are typically 50-200+ pages. Must extract all pages.
        """
        fetcher = LegislationFetcher()

        content = await fetcher.fetch_async("/au-victoria/ohs/2004", force=True)

        # OHS Act should have multiple parts and divisions
        assert "part" in content.lower()
        assert "division" in content.lower()

        # Should have content from throughout the document
        # (not just first few pages)
        assert content.count("\n") > 1000  # Many lines of text

        fetcher.close()

    @pytest.mark.asyncio
    async def test_cached_pdf_content_includes_citation_metadata(self) -> None:
        """Test that cached content has traceable source information.

        When legislation is retrieved from cache, user must be able to
        trace back to original PDF source for verification.
        """
        fetcher = LegislationFetcher()

        # Fetch once (caches)
        await fetcher.fetch_async("/au-victoria/ohs/2004", force=True)

        # Fetch again from cache
        content = await fetcher.fetch_async("/au-victoria/ohs/2004", force=False)

        # Content should have header with source info
        assert "Occupational Health and Safety Act 2004" in content

        # Metadata should be retrievable
        from mcp_fair_shake.canonical_id import parse_canonical_id

        canonical = parse_canonical_id("/au-victoria/ohs/2004")
        assert canonical is not None

        metadata = fetcher.cache_manager.read_metadata(canonical)
        assert metadata is not None
        assert metadata.source_url
        assert metadata.fetch_timestamp  # fetched_at is stored as fetch_timestamp

        fetcher.close()

    def test_pdf_parser_preserves_section_structure(self) -> None:
        """Test that PDF parser preserves legislation structure.

        Must preserve:
        - Part/Division/Section numbering
        - Headings and subheadings
        - Paragraph structure

        NOTE: This test uses a real PDF fetch to verify structure preservation.
        """
        fetcher = LegislationFetcher()

        # Use the actual OHS Act PDF (cached from previous tests)
        import asyncio

        content = asyncio.run(fetcher.fetch_async("/au-victoria/ohs/2004", force=False))

        # Must preserve section numbers (Section 21 is a key provision)
        assert "21" in content

        # Must preserve Part/Division structure
        assert "Part" in content or "part" in content.lower()

        # Must preserve headings
        assert "Duties" in content or "duties" in content.lower()

        # Must have page markers for citation
        assert "[Page" in content

        fetcher.close()


class TestPdfDownload:
    """Test PDF download functionality."""

    @pytest.mark.asyncio
    async def test_download_pdf_from_victorian_legislation_site(self) -> None:
        """Test downloading PDF from legislation.vic.gov.au.

        Must download actual PDF file and verify it's a valid PDF.
        """
        fetcher = LegislationFetcher()

        # Get PDF URL for OHS Act
        source_info = fetcher.get_source_info("/au-victoria/ohs/2004")
        assert source_info is not None

        # URL should point to a PDF file
        pdf_url = source_info["url"]
        assert ".pdf" in pdf_url.lower() or "PDF" in pdf_url

        # Download should work
        pdf_bytes = await fetcher._download_pdf(pdf_url)

        # Must be a valid PDF (starts with %PDF-)
        assert pdf_bytes.startswith(b"%PDF-")

        # Must be substantial size (Victorian Acts are typically 1-2MB)
        assert len(pdf_bytes) > 100000  # At least 100KB

        fetcher.close()
