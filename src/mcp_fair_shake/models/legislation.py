"""Pydantic models for legislation structure.

Provides type-safe representations of legislative hierarchy:
Act → Part → Division → Section → Subsection → Paragraph
"""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class CitationType(str, Enum):
    """Types of legal citations."""

    ACT = "act"
    PART = "part"
    DIVISION = "division"
    SECTION = "section"
    SUBSECTION = "subsection"
    PARAGRAPH = "paragraph"
    REGULATION = "regulation"
    ARTICLE = "article"
    CLAUSE = "clause"  # For Modern Awards


class LegislationNode(BaseModel):
    """Base node for all legislation elements."""

    id: str  # Canonical ID (e.g., "/au-federal/fwa/2009/s394")
    type: CitationType
    number: str | None = None  # Section number (e.g., "394"), Part number (e.g., "3-2")
    title: str
    content: str  # The actual legal text
    parent_id: str | None = None
    children_ids: list[str] = Field(default_factory=list)

    # Metadata
    enacted_date: date | None = None
    effective_date: date | None = None
    amended_dates: list[date] = Field(default_factory=list)
    repealed_date: date | None = None

    # Cross-references
    references: list[str] = Field(default_factory=list)  # IDs this node cites
    referenced_by: list[str] = Field(default_factory=list)  # IDs that cite this node


class Act(LegislationNode):
    """Top-level Act."""

    type: CitationType = CitationType.ACT
    jurisdiction: str  # "au-federal", "au-victoria", etc.
    year: int
    parts: list[str] = Field(default_factory=list)  # Part IDs
    sections: list[str] = Field(default_factory=list)  # Direct section IDs (for Acts without Parts)


class Part(LegislationNode):
    """Part of an Act."""

    type: CitationType = CitationType.PART
    act_id: str
    part_number: str  # "1-1", "2-3", "3-2"
    divisions: list[str] = Field(default_factory=list)
    sections: list[str] = Field(default_factory=list)  # Direct sections (if no divisions)


class Division(LegislationNode):
    """Division within a Part."""

    type: CitationType = CitationType.DIVISION
    part_id: str
    division_number: str  # "1", "2", "3"
    sections: list[str] = Field(default_factory=list)


class Section(LegislationNode):
    """Section of legislation (most important for citations)."""

    type: CitationType = CitationType.SECTION
    division_id: str | None = None  # Optional - some sections are direct under Part or Act
    part_id: str | None = None  # Optional
    act_id: str
    section_number: str  # "394", "21", "1"
    subsections: list[str] = Field(default_factory=list)

    @property
    def canonical_id(self) -> str:
        """Generate canonical ID for this section."""
        return f"{self.act_id}/s{self.section_number}"


class Subsection(LegislationNode):
    """Subsection within a Section."""

    type: CitationType = CitationType.SUBSECTION
    section_id: str
    subsection_number: str  # "1", "2", "2a"
    paragraphs: list[str] = Field(default_factory=list)


class Paragraph(LegislationNode):
    """Paragraph within a Subsection or Section."""

    type: CitationType = CitationType.PARAGRAPH
    subsection_id: str | None = None  # Optional - can be direct child of Section
    paragraph_letter: str  # "a", "b", "c", "aa", "ba"
