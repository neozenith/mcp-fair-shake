"""Parser for Federal legislation in structured text format.

Parses legislation from legislation.gov.au that has been extracted into
markdown-like structured text format.
"""

import logging
import re
from typing import Any

from mcp_fair_shake.models import Act, CitationType, Division, LegislationNode, Part, Paragraph, Section, Subsection

log = logging.getLogger(__name__)


class FederalTextParser:
    """Parser for Federal legislation in structured text format."""

    def __init__(self) -> None:
        """Initialize parser with empty registry."""
        self.registry: dict[str, LegislationNode] = {}

    def can_parse(self, url: str, content_type: str) -> bool:
        """Check if this parser can handle the given URL and content type."""
        return "legislation.gov.au" in url and "text" in content_type.lower()

    def parse(self, content: bytes, metadata: dict[str, Any]) -> tuple[Act, dict[str, LegislationNode]]:
        """Parse Federal legislation text into structured Act.

        Args:
            content: Text content of legislation
            metadata: Dict with 'canonical_id', 'jurisdiction', 'year', 'title'

        Returns:
            Tuple of (Act object, registry dict mapping IDs to nodes)

        Raises:
            ValueError: If required metadata missing
        """
        # Reset registry for new parse
        self.registry = {}

        # Validate metadata
        required = ["canonical_id", "jurisdiction", "year", "title"]
        missing = [k for k in required if k not in metadata]
        if missing:
            raise ValueError(f"Missing required metadata: {missing}")

        # Decode content
        text = content.decode("utf-8")

        # Preprocess: Split "Collapse" markers and section numbers onto separate lines
        # The Fair Work Act has all markers and sections collapsed on long lines
        text = re.sub(r"(Collapse)", r"\n\1", text)  # Split Collapse markers
        text = re.sub(r"(\d+[A-Z]*)\s\s", r"\n\1  ", text)  # Split section numbers (e.g., "10  ")

        lines = text.split("\n")

        # Create Act
        act = Act(
            id=metadata["canonical_id"],
            title=metadata["title"],
            content="",  # Will be populated from text
            jurisdiction=metadata["jurisdiction"],
            year=metadata["year"],
        )
        self.registry[act.id] = act

        # Parse hierarchy
        self._parse_hierarchy(lines, act)

        return act, self.registry

    def _parse_hierarchy(self, lines: list[str], act: Act) -> None:
        """Parse legislation hierarchy using state machine.

        Args:
            lines: Lines of text
            act: Act object to populate
        """
        current_part: Part | None = None
        current_division: Division | None = None
        current_section: Section | None = None
        collecting_content = False
        content_lines: list[str] = []

        for line in lines:
            line = line.rstrip()

            # Skip empty lines and navigation
            if not line or line.startswith("-"):
                continue

            # Part marker: "CollapsePart 1-1—Introduction" or "CollapsePart 1‑1—Introduction"
            # Note: May use regular hyphen (-) or non-breaking hyphen (‑ U+2011)
            part_match = re.match(r"^Collapse(Part [\d\-‑]+)[—\-](.+)$", line)
            if part_match:
                # Save previous section content
                if current_section and content_lines:
                    current_section.content = "\n".join(content_lines)
                    # Extract subsections and paragraphs
                    self._extract_subsections(current_section)
                    content_lines = []

                part_number, part_title = part_match.groups()
                part_number = part_number.replace("Part ", "")
                part_id = f"{act.id}/part-{part_number}"

                current_part = Part(
                    id=part_id,
                    title=f"Part {part_number}—{part_title}",
                    content="",
                    act_id=act.id,
                    part_number=part_number,
                    parent_id=act.id,
                )
                self.registry[part_id] = current_part
                act.parts.append(part_id)
                act.children_ids.append(part_id)
                current_division = None
                continue

            # Division marker: "CollapseDivision 1—Preliminary"
            # Note: May use em dash (— U+2014) or regular hyphen
            div_match = re.match(r"^Collapse(Division \d+)[—\-](.+)$", line)
            if div_match:
                # Save previous section content
                if current_section and content_lines:
                    current_section.content = "\n".join(content_lines)
                    # Extract subsections and paragraphs
                    self._extract_subsections(current_section)
                    content_lines = []

                div_number, div_title = div_match.groups()
                div_number = div_number.replace("Division ", "")

                if current_part:
                    div_id = f"{current_part.id}/div-{div_number}"
                    current_division = Division(
                        id=div_id,
                        title=f"Division {div_number}—{div_title}",
                        content="",
                        part_id=current_part.id,
                        division_number=div_number,
                        parent_id=current_part.id,
                    )
                    self.registry[div_id] = current_division
                    current_part.divisions.append(div_id)
                    current_part.children_ids.append(div_id)
                continue

            # Section marker: "1  Short title" or "15AA  Determining..."
            section_match = re.match(r"^(\d+[A-Z]*)\s\s(.+)$", line)
            if section_match:
                # Save previous section content
                if current_section and content_lines:
                    current_section.content = "\n".join(content_lines)
                    # Extract subsections and paragraphs
                    self._extract_subsections(current_section)
                    content_lines = []

                section_number, section_title = section_match.groups()
                section_id = f"{act.id}/s{section_number}"

                current_section = Section(
                    id=section_id,
                    title=section_title,
                    content="",  # Will be populated
                    act_id=act.id,
                    section_number=section_number,
                    part_id=current_part.id if current_part else None,
                    division_id=current_division.id if current_division else None,
                    parent_id=(current_division.id if current_division
                              else current_part.id if current_part
                              else act.id),
                )
                self.registry[section_id] = current_section

                # Add to appropriate parent
                if current_division:
                    current_division.sections.append(section_id)
                    current_division.children_ids.append(section_id)
                elif current_part:
                    current_part.sections.append(section_id)
                    current_part.children_ids.append(section_id)
                else:
                    act.sections.append(section_id)
                    act.children_ids.append(section_id)

                collecting_content = True
                continue

            # Collect section content
            if collecting_content and current_section:
                content_lines.append(line)

        # Save last section
        if current_section and content_lines:
            current_section.content = "\n".join(content_lines)
            self._extract_subsections(current_section)

    def _extract_subsections(self, section: Section) -> None:
        """Extract subsections and paragraphs from section content.

        Args:
            section: Section to extract subsections from
        """
        if not section.content:
            return

        lines = section.content.split("\n")
        current_subsection: Subsection | None = None
        current_paragraph: Paragraph | None = None
        content_lines: list[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Subsection marker: "(1)" or "(2a)" - may or may not have space after ")"
            subsec_match = re.match(r"^\((\d+[a-z]*)\)(.+)$", line)
            if subsec_match:
                # Save previous paragraph content
                if current_paragraph and content_lines:
                    # Append collected lines to paragraph content
                    current_paragraph.content += " " + " ".join(content_lines)
                    content_lines = []
                # Save previous subsection content
                elif current_subsection and content_lines:
                    # Append collected lines to subsection content
                    current_subsection.content += " " + " ".join(content_lines)
                    content_lines = []

                subsec_number, subsec_content = subsec_match.groups()
                subsec_id = f"{section.id}/{subsec_number}"

                current_subsection = Subsection(
                    id=subsec_id,
                    title="",
                    content=subsec_content,  # Start with initial content
                    section_id=section.id,
                    subsection_number=subsec_number,
                    parent_id=section.id,
                )
                self.registry[subsec_id] = current_subsection
                section.subsections.append(subsec_id)
                section.children_ids.append(subsec_id)
                current_paragraph = None
                continue

            # Paragraph marker: "(a)" or "(aa)" - may or may not have space after ")"
            para_match = re.match(r"^\(([a-z]+)\)(.+)$", line)
            if para_match:
                # Save collected content to previous paragraph or subsection
                if current_paragraph and content_lines:
                    current_paragraph.content += " " + " ".join(content_lines)
                    content_lines = []
                elif current_subsection and content_lines:
                    current_subsection.content += " " + " ".join(content_lines)
                    content_lines = []

                para_letter, para_content = para_match.groups()

                # Determine parent (subsection if exists, otherwise section)
                if current_subsection:
                    para_id = f"{current_subsection.id}/{para_letter}"
                    parent_id = current_subsection.id
                else:
                    # Direct paragraph under section (no subsection)
                    para_id = f"{section.id}/{para_letter}"
                    parent_id = section.id

                current_paragraph = Paragraph(
                    id=para_id,
                    title="",
                    content=para_content,  # Start with initial content
                    subsection_id=current_subsection.id if current_subsection else None,
                    paragraph_letter=para_letter,
                    parent_id=parent_id,
                )
                self.registry[para_id] = current_paragraph

                # Add to appropriate parent
                if current_subsection:
                    current_subsection.paragraphs.append(para_id)
                    current_subsection.children_ids.append(para_id)
                else:
                    section.children_ids.append(para_id)

                continue

            # Continue collecting content
            content_lines.append(line)

        # Save last item's collected content
        if current_paragraph and content_lines:
            current_paragraph.content += " " + " ".join(content_lines)
        elif current_subsection and content_lines:
            current_subsection.content += " " + " ".join(content_lines)
