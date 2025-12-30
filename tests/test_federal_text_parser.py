"""Tests for Federal legislation text parser."""

from pathlib import Path

import pytest

from mcp_fair_shake.models import Act, CitationType
from mcp_fair_shake.parsers import FederalTextParser


@pytest.fixture
def sample_fixture() -> bytes:
    """Load sample Fair Work Act fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "fwa-2009-sample.txt"
    return fixture_path.read_bytes()


@pytest.fixture
def sample_metadata() -> dict:
    """Sample metadata for Fair Work Act 2009."""
    return {
        "canonical_id": "/au-federal/fwa/2009",
        "jurisdiction": "au-federal",
        "year": 2009,
        "title": "Fair Work Act 2009",
    }


@pytest.fixture
def parser() -> FederalTextParser:
    """Create parser instance."""
    return FederalTextParser()


def test_can_parse_federal_legislation(parser: FederalTextParser) -> None:
    """Test parser correctly identifies Federal legislation."""
    assert parser.can_parse("https://legislation.gov.au/Details/C2009A00028", "text/plain")
    assert parser.can_parse("https://legislation.gov.au/Series/C2009A00028", "text")
    assert not parser.can_parse("https://legislation.vic.gov.au/", "text/plain")
    assert not parser.can_parse("https://legislation.gov.au/", "application/pdf")


def test_parse_missing_metadata(parser: FederalTextParser, sample_fixture: bytes) -> None:
    """Test parser raises error for missing required metadata."""
    with pytest.raises(ValueError, match="Missing required metadata"):
        parser.parse(sample_fixture, {"jurisdiction": "au-federal"})


def test_parse_act_metadata(
    parser: FederalTextParser, sample_fixture: bytes, sample_metadata: dict
) -> None:
    """Test Act metadata extraction."""
    act, registry = parser.parse(sample_fixture, sample_metadata)

    assert isinstance(act, Act)
    assert act.id == "/au-federal/fwa/2009"
    assert act.type == CitationType.ACT
    assert act.title == "Fair Work Act 2009"
    assert act.jurisdiction == "au-federal"
    assert act.year == 2009
    assert act.id in registry


def test_parse_parts(
    parser: FederalTextParser, sample_fixture: bytes, sample_metadata: dict
) -> None:
    """Test Part extraction."""
    act, registry = parser.parse(sample_fixture, sample_metadata)

    # Should extract Part 1-1 and Part 3-2
    assert len(act.parts) == 2
    assert "/au-federal/fwa/2009/part-1-1" in act.parts
    assert "/au-federal/fwa/2009/part-3-2" in act.parts
    assert act.parts[0] in act.children_ids
    assert act.parts[1] in act.children_ids

    # Verify Parts are in registry
    assert "/au-federal/fwa/2009/part-1-1" in registry
    assert "/au-federal/fwa/2009/part-3-2" in registry

    from mcp_fair_shake.models import Part
    part_1_1 = registry["/au-federal/fwa/2009/part-1-1"]
    assert isinstance(part_1_1, Part)
    assert part_1_1.part_number == "1-1"
    assert part_1_1.type == CitationType.PART


def test_parse_divisions(
    parser: FederalTextParser, sample_fixture: bytes, sample_metadata: dict
) -> None:
    """Test Division extraction."""
    act, registry = parser.parse(sample_fixture, sample_metadata)

    from mcp_fair_shake.models import Division, Part

    # Part 1-1 should have Division 1 and Division 2
    part_1_1_id = "/au-federal/fwa/2009/part-1-1"
    assert part_1_1_id in registry
    part_1_1 = registry[part_1_1_id]
    assert isinstance(part_1_1, Part)
    assert len(part_1_1.divisions) == 2
    assert f"{part_1_1_id}/div-1" in part_1_1.divisions
    assert f"{part_1_1_id}/div-2" in part_1_1.divisions

    # Verify Division 1 is in registry
    div_1_id = f"{part_1_1_id}/div-1"
    assert div_1_id in registry
    div_1 = registry[div_1_id]
    assert isinstance(div_1, Division)
    assert div_1.division_number == "1"
    assert div_1.type == CitationType.DIVISION

    # Part 3-2 should have Division 1 and Division 3
    part_3_2_id = "/au-federal/fwa/2009/part-3-2"
    assert part_3_2_id in registry
    part_3_2 = registry[part_3_2_id]
    assert isinstance(part_3_2, Part)
    assert len(part_3_2.divisions) == 2
    assert f"{part_3_2_id}/div-1" in part_3_2.divisions
    assert f"{part_3_2_id}/div-3" in part_3_2.divisions


def test_parse_sections(
    parser: FederalTextParser, sample_fixture: bytes, sample_metadata: dict
) -> None:
    """Test Section extraction."""
    act, registry = parser.parse(sample_fixture, sample_metadata)

    from mcp_fair_shake.models import Section

    # Should extract sections 1, 2, 3, 5, 382, 394, 15AA
    expected_sections = [
        "/au-federal/fwa/2009/s1",
        "/au-federal/fwa/2009/s2",
        "/au-federal/fwa/2009/s3",
        "/au-federal/fwa/2009/s5",
        "/au-federal/fwa/2009/s382",
        "/au-federal/fwa/2009/s394",
        "/au-federal/fwa/2009/s15AA",
    ]

    # Check that all sections are in registry
    for section_id in expected_sections:
        assert section_id in registry, f"Section {section_id} not found in registry"
        section = registry[section_id]
        assert isinstance(section, Section)
        assert section.type == CitationType.SECTION

    # Verify section 1 has correct title
    section_1 = registry["/au-federal/fwa/2009/s1"]
    assert section_1.title == "Short title"
    assert section_1.section_number == "1"


def test_parse_subsections(
    parser: FederalTextParser, sample_fixture: bytes, sample_metadata: dict
) -> None:
    """Test Subsection extraction for fine-grained structure."""
    act, registry = parser.parse(sample_fixture, sample_metadata)

    from mcp_fair_shake.models import Section, Subsection

    # Section 2 should have subsections (1) and (2)
    section_2_id = "/au-federal/fwa/2009/s2"
    section_2 = registry[section_2_id]
    assert isinstance(section_2, Section)
    assert len(section_2.subsections) == 2
    assert f"{section_2_id}/1" in section_2.subsections
    assert f"{section_2_id}/2" in section_2.subsections

    # Verify subsection objects exist in registry
    subsec_2_1 = registry[f"{section_2_id}/1"]
    assert isinstance(subsec_2_1, Subsection)
    assert subsec_2_1.type == CitationType.SUBSECTION
    assert subsec_2_1.subsection_number == "1"

    # Section 3 should have subsections (1) and (2)
    section_3_id = "/au-federal/fwa/2009/s3"
    section_3 = registry[section_3_id]
    assert len(section_3.subsections) == 2

    # Section 394 should have subsections (1), (2), (3)
    section_394_id = "/au-federal/fwa/2009/s394"
    section_394 = registry[section_394_id]
    assert len(section_394.subsections) == 3
    assert f"{section_394_id}/1" in section_394.subsections
    assert f"{section_394_id}/2" in section_394.subsections
    assert f"{section_394_id}/3" in section_394.subsections

    # Section 15AA should have subsections (1), (2)
    section_15AA_id = "/au-federal/fwa/2009/s15AA"
    section_15AA = registry[section_15AA_id]
    assert len(section_15AA.subsections) == 2


def test_parse_paragraphs(
    parser: FederalTextParser, sample_fixture: bytes, sample_metadata: dict
) -> None:
    """Test Paragraph extraction for finest-granule structure."""
    act, registry = parser.parse(sample_fixture, sample_metadata)

    from mcp_fair_shake.models import Paragraph, Subsection

    # Section 3, subsection (1) should have paragraphs (a), (b), (c)
    section_3_subsec_1_id = "/au-federal/fwa/2009/s3/1"
    subsec_3_1 = registry[section_3_subsec_1_id]
    assert isinstance(subsec_3_1, Subsection)
    assert len(subsec_3_1.paragraphs) == 3
    assert f"{section_3_subsec_1_id}/a" in subsec_3_1.paragraphs
    assert f"{section_3_subsec_1_id}/b" in subsec_3_1.paragraphs
    assert f"{section_3_subsec_1_id}/c" in subsec_3_1.paragraphs

    # Verify paragraph objects exist
    para_a = registry[f"{section_3_subsec_1_id}/a"]
    assert isinstance(para_a, Paragraph)
    assert para_a.type == CitationType.PARAGRAPH
    assert para_a.paragraph_letter == "a"

    # Section 394, subsection (2) should have paragraphs (a), (b), (c)
    section_394_subsec_2_id = "/au-federal/fwa/2009/s394/2"
    subsec_394_2 = registry[section_394_subsec_2_id]
    assert len(subsec_394_2.paragraphs) == 3
    assert f"{section_394_subsec_2_id}/a" in subsec_394_2.paragraphs
    assert f"{section_394_subsec_2_id}/b" in subsec_394_2.paragraphs
    assert f"{section_394_subsec_2_id}/c" in subsec_394_2.paragraphs

    # Section 394, subsection (3) should have paragraphs (a), (b)
    section_394_subsec_3_id = "/au-federal/fwa/2009/s394/3"
    subsec_394_3 = registry[section_394_subsec_3_id]
    assert len(subsec_394_3.paragraphs) == 2

    # Section 15AA, subsection (2) should have paragraphs (a), (b), (c), (d)
    section_15AA_subsec_2_id = "/au-federal/fwa/2009/s15AA/2"
    subsec_15AA_2 = registry[section_15AA_subsec_2_id]
    assert len(subsec_15AA_2.paragraphs) == 4
    for letter in ["a", "b", "c", "d"]:
        para_id = f"{section_15AA_subsec_2_id}/{letter}"
        assert para_id in subsec_15AA_2.paragraphs
        assert para_id in registry


def test_hierarchy_integrity(
    parser: FederalTextParser, sample_fixture: bytes, sample_metadata: dict
) -> None:
    """Test parent-child relationships are correct throughout hierarchy."""
    act, registry = parser.parse(sample_fixture, sample_metadata)

    from mcp_fair_shake.models import Division, Part, Section, Subsection

    # Act should have parts in children_ids
    assert len(act.parts) > 0
    assert all(part_id in act.children_ids for part_id in act.parts)

    # Verify Parts link correctly
    for part_id in act.parts:
        part = registry[part_id]
        assert isinstance(part, Part)
        assert part.parent_id == act.id
        assert part.act_id == act.id

    # Verify Divisions link correctly
    part_1_1 = registry["/au-federal/fwa/2009/part-1-1"]
    for div_id in part_1_1.divisions:
        div = registry[div_id]
        assert isinstance(div, Division)
        assert div.parent_id == part_1_1.id
        assert div.part_id == part_1_1.id

    # Verify Sections link correctly
    div_1_id = "/au-federal/fwa/2009/part-1-1/div-1"
    div_1 = registry[div_1_id]
    for section_id in div_1.sections:
        section = registry[section_id]
        assert isinstance(section, Section)
        assert section.parent_id == div_1.id
        assert section.division_id == div_1.id

    # Verify Subsections link correctly
    section_2 = registry["/au-federal/fwa/2009/s2"]
    for subsec_id in section_2.subsections:
        subsec = registry[subsec_id]
        assert isinstance(subsec, Subsection)
        assert subsec.parent_id == section_2.id
        assert subsec.section_id == section_2.id


@pytest.mark.parametrize(
    ("section_num", "expected_title"),
    [
        ("1", "Short title"),
        ("2", "Commencement"),
        ("3", "Definitions"),
        ("5", "Objects of this Act"),
        ("382", "Meaning of unfair dismissal"),
        ("394", "Criteria for considering harshness etc."),
        ("15AA", "Determining the base rate of pay"),
    ],
)
def test_section_titles(
    parser: FederalTextParser,
    sample_fixture: bytes,
    sample_metadata: dict,
    section_num: str,
    expected_title: str,
) -> None:
    """Test section titles are correctly extracted."""
    act, registry = parser.parse(sample_fixture, sample_metadata)

    from mcp_fair_shake.models import Section

    # Find section by ID in the registry
    section_id = f"/au-federal/fwa/2009/s{section_num}"
    assert section_id in registry, f"Section {section_num} not found"

    section = registry[section_id]
    assert isinstance(section, Section)
    assert section.title == expected_title
    assert section.section_number == section_num


def test_content_extraction(
    parser: FederalTextParser, sample_fixture: bytes, sample_metadata: dict
) -> None:
    """Test section content is correctly extracted."""
    act, registry = parser.parse(sample_fixture, sample_metadata)

    from mcp_fair_shake.models import Section

    # Section 1 should have content "This Act may be cited as the Fair Work Act 2009."
    section_1_id = "/au-federal/fwa/2009/s1"
    section_1 = registry[section_1_id]
    assert isinstance(section_1, Section)
    assert "Fair Work Act 2009" in section_1.content

    # Section 2 content should be split into subsections, not in section.content
    section_2 = registry["/au-federal/fwa/2009/s2"]
    # Content is extracted to subsections, so section.content might be empty or contain pre-subsection text

    # Subsection 2(1) should have content about commencement
    subsec_2_1 = registry["/au-federal/fwa/2009/s2/1"]
    assert "column" in subsec_2_1.content.lower()

    # Paragraph 3(1)(a) should have content about "modern award"
    para_3_1_a = registry["/au-federal/fwa/2009/s3/1/a"]
    assert "modern award" in para_3_1_a.content.lower()
