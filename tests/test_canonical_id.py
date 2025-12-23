"""Tests for canonical ID parsing and validation."""

import pytest

from mcp_fair_shake.canonical_id import (
    CanonicalID,
    build_canonical_id,
    parse_canonical_id,
    validate_canonical_id,
)


class TestParseCanonicalID:
    """Test canonical ID parsing."""

    def test_parse_valid_id_with_section(self) -> None:
        """Test parsing a valid ID with section."""
        result = parse_canonical_id("/au-victoria/ohs/2004/s21")

        assert result is not None
        assert result.jurisdiction == "au-victoria"
        assert result.code_type == "ohs"
        assert result.year == "2004"
        assert result.section == "s21"

    def test_parse_valid_id_without_section(self) -> None:
        """Test parsing a valid ID without section."""
        result = parse_canonical_id("/au-federal/fwa/2009")

        assert result is not None
        assert result.jurisdiction == "au-federal"
        assert result.code_type == "fwa"
        assert result.year == "2009"
        assert result.section is None

    @pytest.mark.parametrize(
        ("canonical_id", "jurisdiction", "code_type", "year", "section"),
        [
            ("/au-federal/fwa/2009/s394", "au-federal", "fwa", "2009", "s394"),
            ("/au-victoria/ohs/2004/s21", "au-victoria", "ohs", "2004", "s21"),
            ("/au-victoria/eoa/2010", "au-victoria", "eoa", "2010", None),
            ("/au-federal/fwr/2009/reg3.01", "au-federal", "fwr", "2009", "reg3.01"),
        ],
    )
    def test_parse_various_ids(
        self,
        canonical_id: str,
        jurisdiction: str,
        code_type: str,
        year: str,
        section: str | None,
    ) -> None:
        """Test parsing various canonical IDs."""
        result = parse_canonical_id(canonical_id)

        assert result is not None
        assert result.jurisdiction == jurisdiction
        assert result.code_type == code_type
        assert result.year == year
        assert result.section == section

    def test_parse_invalid_jurisdiction(self) -> None:
        """Test parsing with invalid jurisdiction."""
        result = parse_canonical_id("/invalid/ohs/2004/s21")
        assert result is None

    def test_parse_invalid_code_type(self) -> None:
        """Test parsing with invalid code type."""
        result = parse_canonical_id("/au-victoria/invalid/2004/s21")
        assert result is None

    def test_parse_invalid_format(self) -> None:
        """Test parsing with invalid format."""
        assert parse_canonical_id("not-a-canonical-id") is None
        assert parse_canonical_id("/au-victoria") is None
        assert parse_canonical_id("/au-victoria/ohs") is None
        assert parse_canonical_id("au-victoria/ohs/2004") is None  # Missing leading /


class TestValidateCanonicalID:
    """Test canonical ID validation."""

    def test_validate_valid_ids(self) -> None:
        """Test validation of valid IDs."""
        assert validate_canonical_id("/au-victoria/ohs/2004/s21") is True
        assert validate_canonical_id("/au-federal/fwa/2009") is True

    def test_validate_invalid_ids(self) -> None:
        """Test validation of invalid IDs."""
        assert validate_canonical_id("/invalid/ohs/2004") is False
        assert validate_canonical_id("not-valid") is False
        assert validate_canonical_id("") is False


class TestBuildCanonicalID:
    """Test building canonical IDs from components."""

    def test_build_without_section(self) -> None:
        """Test building ID without section."""
        result = build_canonical_id("au-victoria", "ohs", "2004")
        assert result == "/au-victoria/ohs/2004"

    def test_build_with_section(self) -> None:
        """Test building ID with section."""
        result = build_canonical_id("au-victoria", "ohs", "2004", "s21")
        assert result == "/au-victoria/ohs/2004/s21"

    def test_build_invalid_jurisdiction(self) -> None:
        """Test building with invalid jurisdiction."""
        with pytest.raises(ValueError, match="Invalid jurisdiction"):
            build_canonical_id("invalid", "ohs", "2004")

    def test_build_invalid_code_type(self) -> None:
        """Test building with invalid code type."""
        with pytest.raises(ValueError, match="Invalid code type"):
            build_canonical_id("au-victoria", "invalid", "2004")


class TestCanonicalIDClass:
    """Test CanonicalID dataclass."""

    def test_full_id_property(self) -> None:
        """Test full_id property."""
        cid = CanonicalID("au-victoria", "ohs", "2004", "s21")
        assert cid.full_id == "/au-victoria/ohs/2004/s21"

        cid_no_section = CanonicalID("au-victoria", "ohs", "2004")
        assert cid_no_section.full_id == "/au-victoria/ohs/2004"

    def test_code_name_property(self) -> None:
        """Test code_name property."""
        cid = CanonicalID("au-victoria", "ohs", "2004")
        assert cid.code_name == "Occupational Health and Safety Act"

        cid_fwa = CanonicalID("au-federal", "fwa", "2009")
        assert cid_fwa.code_name == "Fair Work Act"

    def test_cache_filename_property(self) -> None:
        """Test cache_filename property."""
        cid = CanonicalID("au-victoria", "ohs", "2004")
        assert cid.cache_filename == "ohs-2004.txt"

    def test_metadata_filename_property(self) -> None:
        """Test metadata_filename property."""
        cid = CanonicalID("au-victoria", "ohs", "2004")
        assert cid.metadata_filename == "ohs-2004-metadata.json"

    def test_checksum_filename_property(self) -> None:
        """Test checksum_filename property."""
        cid = CanonicalID("au-victoria", "ohs", "2004")
        assert cid.checksum_filename == "ohs-2004.checksum"

    def test_str_method(self) -> None:
        """Test __str__ method."""
        cid = CanonicalID("au-victoria", "ohs", "2004", "s21")
        assert str(cid) == "/au-victoria/ohs/2004/s21"
