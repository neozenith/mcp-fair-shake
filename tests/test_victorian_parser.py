"""Tests for Victorian legislation parser."""

import pytest

from mcp_fair_shake.parsers.victorian_text import VictorianTextParser


# Sample Victorian text fixture (based on actual OHS Act 2004)
VICTORIAN_SAMPLE = """[Page 11]

Authorised by the Chief Parliamentary Counsel

1
Authorised Version No. 045
Occupational Health and Safety Act 2004
No. 107 of 2004
Authorised Version incorporating amendments as at
6 August 2025
The Parliament of Victoria enacts as follows:
Part 1—Preliminary
 1 Purposes
The main purposes of this Act are—
 (a) to create a legislative framework to give
effect to the objects of this Act; and
 (b) to repeal the Occupational Health and
Safety Act 1985; and
 (c) to provide for matters of a transitional nature
and make consequential amendments.
 2 Objects
 (1) The objects of this Act are—
 (a) to secure the health, safety and welfare of
employees and other persons at work; and
 (b) to eliminate, at the source, risks to the health,
safety or welfare of employees and other
persons at work; and
 (c) to ensure that the health and safety of
members of the public is not placed at risk
by the conduct of undertakings by employers
and self-employed persons; and

[Page 12]

Authorised by the Chief Parliamentary Counsel
Part 1—Preliminary



Occupational Health and Safety Act 2004
No. 107 of 2004
2
 (d) to provide for the involvement of employees,
employers, and organisations representing
those persons, in the formulation and
implementation of health, safety and welfare
standards—
having regard to the principles of health and
safety protection set out in section 4.
 (2) It is the intention of the Parliament that in the
administration of this Act regard should be had to
the principles of health and safety protection set
out in section 4.

Part 2—The Authority
Division 1—General functions and powers
 7 Functions of the Authority
 (1) The Authority has the following functions—
 (a) to enquire into and report to the Minister on
any matters referred to the Authority by the
Minister (within the time specified by the
Minister);
 (b) to make recommendations to the Minister
with respect to—
 (i) the operation and administration of this
Act and the regulations; and
 (ii) regulations or compliance codes that
the Minister or the Authority proposes
should be made or approved under this
Act; and
S. 7(1)(b)
amended by
No. 28/2005
s. 5.
"""


class TestVictorianTextParser:
    """Test Victorian legislation parser."""

    def test_can_parse_victorian_url(self) -> None:
        """Test can_parse returns True for Victorian legislation URLs."""
        parser = VictorianTextParser()
        assert parser.can_parse(
            "https://legislation.vic.gov.au/in-force/acts/occupational-health-and-safety-act-2004/045",
            "text/html",
        )

    def test_can_parse_rejects_non_victorian(self) -> None:
        """Test can_parse returns False for non-Victorian URLs."""
        parser = VictorianTextParser()
        assert not parser.can_parse("https://legislation.gov.au/C2009A00028", "text/html")

    def test_parse_requires_metadata(self) -> None:
        """Test parse raises ValueError if required metadata missing."""
        parser = VictorianTextParser()
        with pytest.raises(ValueError, match="Missing required metadata"):
            parser.parse(b"content", {})

    def test_preprocess_removes_page_markers(self) -> None:
        """Test preprocessing removes page markers."""
        parser = VictorianTextParser()
        text = "[Page 11]\nSome content\n[Page 12]\nMore content"
        cleaned = parser._preprocess_pdf_artifacts(text)
        assert "[Page 11]" not in cleaned
        assert "[Page 12]" not in cleaned
        assert "Some content" in cleaned
        assert "More content" in cleaned

    def test_preprocess_removes_headers(self) -> None:
        """Test preprocessing removes headers/footers."""
        parser = VictorianTextParser()
        text = "Authorised by the Chief Parliamentary Counsel\nSome content"
        cleaned = parser._preprocess_pdf_artifacts(text)
        assert "Authorised by the Chief Parliamentary Counsel" not in cleaned
        assert "Some content" in cleaned

    def test_preprocess_keeps_amendment_notes(self) -> None:
        """Test preprocessing keeps amendment notes."""
        parser = VictorianTextParser()
        text = "S. 7(1)(b) amended by No. 28/2005 s. 5.\nSome content"
        cleaned = parser._preprocess_pdf_artifacts(text)
        assert "S. 7(1)(b) amended by" in cleaned
        assert "Some content" in cleaned

    def test_is_roman_numeral(self) -> None:
        """Test roman numeral detection."""
        parser = VictorianTextParser()
        # Roman numerals
        assert parser._is_roman_numeral("i")
        assert parser._is_roman_numeral("ii")
        assert parser._is_roman_numeral("iii")
        assert parser._is_roman_numeral("iv")
        assert parser._is_roman_numeral("v")
        assert parser._is_roman_numeral("vi")
        assert parser._is_roman_numeral("vii")
        assert parser._is_roman_numeral("viii")
        assert parser._is_roman_numeral("ix")
        assert parser._is_roman_numeral("x")
        # Not roman numerals
        assert not parser._is_roman_numeral("a")
        assert not parser._is_roman_numeral("b")
        assert not parser._is_roman_numeral("aa")
        assert not parser._is_roman_numeral("z")

    def test_parse_basic_structure(self) -> None:
        """Test parsing basic Act structure."""
        parser = VictorianTextParser()
        metadata = {
            "canonical_id": "/au-victoria/ohs/2004",
            "jurisdiction": "Victoria",
            "year": 2004,
            "title": "Occupational Health and Safety Act 2004",
        }

        act, registry = parser.parse(VICTORIAN_SAMPLE.encode("utf-8"), metadata)

        # Check Act
        assert act.id == "/au-victoria/ohs/2004"
        assert act.title == "Occupational Health and Safety Act 2004"
        assert act.jurisdiction == "Victoria"
        assert act.year == 2004  # year is an integer in the model

        # Check Parts
        assert len(act.parts) == 2
        assert "/au-victoria/ohs/2004/part-1" in act.parts
        assert "/au-victoria/ohs/2004/part-2" in act.parts

        # Check Part 1
        part1 = registry["/au-victoria/ohs/2004/part-1"]
        assert part1.title == "Part 1—Preliminary"
        assert part1.part_number == "1"

        # Check Part 2
        part2 = registry["/au-victoria/ohs/2004/part-2"]
        assert part2.title == "Part 2—The Authority"
        assert part2.part_number == "2"

    def test_parse_divisions(self) -> None:
        """Test parsing Divisions within Parts."""
        parser = VictorianTextParser()
        metadata = {
            "canonical_id": "/au-victoria/ohs/2004",
            "jurisdiction": "Victoria",
            "year": 2004,
            "title": "Occupational Health and Safety Act 2004",
        }

        act, registry = parser.parse(VICTORIAN_SAMPLE.encode("utf-8"), metadata)

        # Check Part 2 has Division
        part2 = registry["/au-victoria/ohs/2004/part-2"]
        assert len(part2.divisions) == 1
        assert "/au-victoria/ohs/2004/part-2/div-1" in part2.divisions

        # Check Division 1
        div1 = registry["/au-victoria/ohs/2004/part-2/div-1"]
        assert div1.title == "Division 1—General functions and powers"
        assert div1.division_number == "1"

    def test_parse_sections(self) -> None:
        """Test parsing Sections."""
        parser = VictorianTextParser()
        metadata = {
            "canonical_id": "/au-victoria/ohs/2004",
            "jurisdiction": "Victoria",
            "year": 2004,
            "title": "Occupational Health and Safety Act 2004",
        }

        act, registry = parser.parse(VICTORIAN_SAMPLE.encode("utf-8"), metadata)

        # Section 1 under Part 1 (no division)
        assert "/au-victoria/ohs/2004/s1" in registry
        section1 = registry["/au-victoria/ohs/2004/s1"]
        assert section1.title == "Purposes"
        assert section1.section_number == "1"
        assert section1.part_id == "/au-victoria/ohs/2004/part-1"
        assert section1.division_id is None

        # Section 2 under Part 1
        assert "/au-victoria/ohs/2004/s2" in registry
        section2 = registry["/au-victoria/ohs/2004/s2"]
        assert section2.title == "Objects"
        assert section2.section_number == "2"

        # Section 7 under Part 2, Division 1
        assert "/au-victoria/ohs/2004/s7" in registry
        section7 = registry["/au-victoria/ohs/2004/s7"]
        assert section7.title == "Functions of the Authority"
        assert section7.section_number == "7"
        assert section7.part_id == "/au-victoria/ohs/2004/part-2"
        assert section7.division_id == "/au-victoria/ohs/2004/part-2/div-1"

    def test_parse_subsections(self) -> None:
        """Test parsing Subsections within Sections."""
        parser = VictorianTextParser()
        metadata = {
            "canonical_id": "/au-victoria/ohs/2004",
            "jurisdiction": "Victoria",
            "year": 2004,
            "title": "Occupational Health and Safety Act 2004",
        }

        act, registry = parser.parse(VICTORIAN_SAMPLE.encode("utf-8"), metadata)

        # Section 2 has subsections
        section2 = registry["/au-victoria/ohs/2004/s2"]
        assert len(section2.subsections) >= 1

        # Check subsection (1)
        subsec1_id = "/au-victoria/ohs/2004/s2/1"
        assert subsec1_id in registry
        subsec1 = registry[subsec1_id]
        assert subsec1.subsection_number == "1"
        assert "objects of this act" in subsec1.content.lower()

        # Check subsection (2)
        subsec2_id = "/au-victoria/ohs/2004/s2/2"
        assert subsec2_id in registry
        subsec2 = registry[subsec2_id]
        assert subsec2.subsection_number == "2"

    def test_parse_paragraphs(self) -> None:
        """Test parsing Paragraphs within Subsections."""
        parser = VictorianTextParser()
        metadata = {
            "canonical_id": "/au-victoria/ohs/2004",
            "jurisdiction": "Victoria",
            "year": 2004,
            "title": "Occupational Health and Safety Act 2004",
        }

        act, registry = parser.parse(VICTORIAN_SAMPLE.encode("utf-8"), metadata)

        # Section 2, subsection (1) has paragraphs (a), (b), (c), (d)
        subsec1 = registry["/au-victoria/ohs/2004/s2/1"]
        assert len(subsec1.paragraphs) >= 3

        # Check paragraph (a)
        para_a_id = "/au-victoria/ohs/2004/s2/1/a"
        assert para_a_id in registry
        para_a = registry[para_a_id]
        assert para_a.paragraph_letter == "a"
        assert "secure the health" in para_a.content.lower()

        # Check paragraph (b)
        para_b_id = "/au-victoria/ohs/2004/s2/1/b"
        assert para_b_id in registry
        para_b = registry[para_b_id]
        assert para_b.paragraph_letter == "b"
        assert "eliminate" in para_b.content.lower()

    def test_parse_nested_paragraphs_with_roman_numerals(self) -> None:
        """Test parsing nested paragraphs with roman numerals (sub-paragraphs)."""
        parser = VictorianTextParser()
        metadata = {
            "canonical_id": "/au-victoria/ohs/2004",
            "jurisdiction": "Victoria",
            "year": 2004,
            "title": "Occupational Health and Safety Act 2004",
        }

        act, registry = parser.parse(VICTORIAN_SAMPLE.encode("utf-8"), metadata)

        # Section 7, subsection (1), paragraph (b) has sub-paragraphs (i), (ii)
        subsec1 = registry["/au-victoria/ohs/2004/s7/1"]

        # Paragraph (b) should exist
        para_b_id = "/au-victoria/ohs/2004/s7/1/b"
        assert para_b_id in registry
        para_b = registry[para_b_id]
        assert para_b.paragraph_letter == "b"

        # Content should include the sub-paragraph text (roman numerals are content, not separate nodes)
        assert "operation and administration" in para_b.content.lower()

    def test_parse_direct_paragraphs_under_section(self) -> None:
        """Test parsing paragraphs directly under sections (no subsection)."""
        parser = VictorianTextParser()
        metadata = {
            "canonical_id": "/au-victoria/ohs/2004",
            "jurisdiction": "Victoria",
            "year": 2004,
            "title": "Occupational Health and Safety Act 2004",
        }

        act, registry = parser.parse(VICTORIAN_SAMPLE.encode("utf-8"), metadata)

        # Section 1 has direct paragraphs (a), (b), (c) with no subsection
        section1 = registry["/au-victoria/ohs/2004/s1"]

        # Should have paragraphs as direct children
        assert len(section1.children_ids) >= 3

        # Check paragraph (a) is direct child of section
        para_a_id = "/au-victoria/ohs/2004/s1/a"
        assert para_a_id in registry
        para_a = registry[para_a_id]
        assert para_a.paragraph_letter == "a"
        assert para_a.subsection_id is None
        assert "legislative framework" in para_a.content.lower()

    def test_registry_completeness(self) -> None:
        """Test that all nodes are in the registry."""
        parser = VictorianTextParser()
        metadata = {
            "canonical_id": "/au-victoria/ohs/2004",
            "jurisdiction": "Victoria",
            "year": 2004,
            "title": "Occupational Health and Safety Act 2004",
        }

        act, registry = parser.parse(VICTORIAN_SAMPLE.encode("utf-8"), metadata)

        # Count nodes
        act_count = 1
        part_count = len(act.parts)
        division_count = sum(len(registry[part_id].divisions) for part_id in act.parts)

        # Count sections
        section_count = 0
        section_count += len(act.sections)  # Direct sections
        for part_id in act.parts:
            part = registry[part_id]
            section_count += len(part.sections)  # Sections under part
            for div_id in part.divisions:
                div = registry[div_id]
                section_count += len(div.sections)  # Sections under division

        # All nodes should be in registry
        assert len(registry) >= act_count + part_count + division_count + section_count
