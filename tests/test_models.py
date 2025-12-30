"""Tests for Pydantic legislation models."""

from datetime import date

import pytest
from pydantic import ValidationError

from mcp_fair_shake.models import (
    Act,
    CitationType,
    Division,
    LegislationNode,
    Paragraph,
    Part,
    Section,
    Subsection,
)


def test_citation_type_enum():
    """Test CitationType enum values."""
    assert CitationType.ACT == "act"
    assert CitationType.SECTION == "section"
    assert CitationType.SUBSECTION == "subsection"
    assert CitationType.PARAGRAPH == "paragraph"


def test_legislation_node_minimal():
    """Test LegislationNode with minimal required fields."""
    node = LegislationNode(
        id="/au-federal/fwa/2009",
        type=CitationType.ACT,
        title="Fair Work Act 2009",
        content="An Act relating to workplace relations",
    )

    assert node.id == "/au-federal/fwa/2009"
    assert node.type == CitationType.ACT
    assert node.title == "Fair Work Act 2009"
    assert node.content == "An Act relating to workplace relations"
    assert node.parent_id is None
    assert node.children_ids == []
    assert node.references == []


def test_legislation_node_with_metadata():
    """Test LegislationNode with full metadata."""
    node = LegislationNode(
        id="/au-federal/fwa/2009",
        type=CitationType.ACT,
        title="Fair Work Act 2009",
        content="An Act relating to workplace relations",
        enacted_date=date(2009, 7, 1),
        effective_date=date(2009, 7, 1),
        amended_dates=[date(2012, 1, 1), date(2015, 7, 1)],
    )

    assert node.enacted_date == date(2009, 7, 1)
    assert node.effective_date == date(2009, 7, 1)
    assert len(node.amended_dates) == 2


def test_act_model():
    """Test Act model with jurisdiction and year."""
    act = Act(
        id="/au-federal/fwa/2009",
        title="Fair Work Act 2009",
        content="An Act relating to workplace relations",
        jurisdiction="au-federal",
        year=2009,
    )

    assert act.type == CitationType.ACT
    assert act.jurisdiction == "au-federal"
    assert act.year == 2009
    assert act.parts == []
    assert act.sections == []


def test_part_model():
    """Test Part model."""
    part = Part(
        id="/au-federal/fwa/2009/part-3-2",
        title="Part 3-2—Unfair dismissal",
        content="This Part provides for protection from unfair dismissal",
        act_id="/au-federal/fwa/2009",
        part_number="3-2",
    )

    assert part.type == CitationType.PART
    assert part.act_id == "/au-federal/fwa/2009"
    assert part.part_number == "3-2"
    assert part.divisions == []
    assert part.sections == []


def test_division_model():
    """Test Division model."""
    division = Division(
        id="/au-federal/fwa/2009/part-3-2/div-3",
        title="Division 3—Remedies",
        content="This Division provides remedies for unfair dismissal",
        part_id="/au-federal/fwa/2009/part-3-2",
        division_number="3",
    )

    assert division.type == CitationType.DIVISION
    assert division.part_id == "/au-federal/fwa/2009/part-3-2"
    assert division.division_number == "3"
    assert division.sections == []


def test_section_model():
    """Test Section model."""
    section = Section(
        id="/au-federal/fwa/2009/s394",
        title="Criteria for considering harshness etc.",
        content="In considering whether a dismissal is harsh, unjust or unreasonable...",
        act_id="/au-federal/fwa/2009",
        section_number="394",
        division_id="/au-federal/fwa/2009/part-3-2/div-3",
        part_id="/au-federal/fwa/2009/part-3-2",
    )

    assert section.type == CitationType.SECTION
    assert section.act_id == "/au-federal/fwa/2009"
    assert section.section_number == "394"
    assert section.canonical_id == "/au-federal/fwa/2009/s394"
    assert section.subsections == []


def test_subsection_model():
    """Test Subsection model."""
    subsection = Subsection(
        id="/au-federal/fwa/2009/s394/1",
        title="",  # Subsections usually don't have titles
        content="The FWC must take into account...",
        section_id="/au-federal/fwa/2009/s394",
        subsection_number="1",
    )

    assert subsection.type == CitationType.SUBSECTION
    assert subsection.section_id == "/au-federal/fwa/2009/s394"
    assert subsection.subsection_number == "1"
    assert subsection.paragraphs == []


def test_paragraph_model():
    """Test Paragraph model."""
    paragraph = Paragraph(
        id="/au-federal/fwa/2009/s394/2/a",
        title="",
        content="whether there was a valid reason for the dismissal related to the person's capacity or conduct",
        subsection_id="/au-federal/fwa/2009/s394/2",
        paragraph_letter="a",
    )

    assert paragraph.type == CitationType.PARAGRAPH
    assert paragraph.subsection_id == "/au-federal/fwa/2009/s394/2"
    assert paragraph.paragraph_letter == "a"


def test_cross_references():
    """Test cross-reference tracking."""
    section = Section(
        id="/au-federal/fwa/2009/s394",
        title="Criteria for considering harshness etc.",
        content="See section 385 for general provisions...",
        act_id="/au-federal/fwa/2009",
        section_number="394",
        references=["/au-federal/fwa/2009/s385"],  # This section cites s385
    )

    assert "/au-federal/fwa/2009/s385" in section.references


def test_parent_child_relationship():
    """Test parent-child relationship tracking."""
    part = Part(
        id="/au-federal/fwa/2009/part-3-2",
        title="Part 3-2—Unfair dismissal",
        content="This Part provides for protection from unfair dismissal",
        act_id="/au-federal/fwa/2009",
        part_number="3-2",
        parent_id="/au-federal/fwa/2009",  # Part's parent is the Act
        divisions=["/au-federal/fwa/2009/part-3-2/div-1", "/au-federal/fwa/2009/part-3-2/div-2"],  # Part's children
    )

    assert part.parent_id == "/au-federal/fwa/2009"
    assert len(part.divisions) == 2


def test_model_serialization():
    """Test model serialization to dict (for JSON export)."""
    section = Section(
        id="/au-federal/fwa/2009/s394",
        title="Criteria for considering harshness etc.",
        content="In considering whether a dismissal is harsh...",
        act_id="/au-federal/fwa/2009",
        section_number="394",
    )

    data = section.model_dump()

    assert data["id"] == "/au-federal/fwa/2009/s394"
    assert data["type"] == "section"
    assert data["section_number"] == "394"
    assert isinstance(data, dict)


def test_model_deserialization():
    """Test model deserialization from dict (for JSON import)."""
    data = {
        "id": "/au-federal/fwa/2009/s394",
        "type": "section",
        "number": "394",
        "title": "Criteria for considering harshness etc.",
        "content": "In considering whether a dismissal is harsh...",
        "parent_id": None,
        "children_ids": [],
        "enacted_date": None,
        "effective_date": None,
        "amended_dates": [],
        "repealed_date": None,
        "references": [],
        "referenced_by": [],
        "division_id": None,
        "part_id": None,
        "act_id": "/au-federal/fwa/2009",
        "section_number": "394",
        "subsections": [],
    }

    section = Section.model_validate(data)

    assert section.id == "/au-federal/fwa/2009/s394"
    assert section.section_number == "394"


def test_validation_error_missing_required_field():
    """Test that ValidationError is raised for missing required fields."""
    with pytest.raises(ValidationError):
        Section(
            # Missing required fields: id, title, content, act_id, section_number
            type=CitationType.SECTION,
        )


def test_validation_error_invalid_type():
    """Test that ValidationError is raised for invalid types."""
    with pytest.raises(ValidationError):
        Act(
            id="/au-federal/fwa/2009",
            title="Fair Work Act 2009",
            content="An Act relating to workplace relations",
            jurisdiction="au-federal",
            year="invalid",  # year should be int, not str
        )
