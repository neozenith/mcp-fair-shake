"""Parser for Victorian legislation in structured text format.

Parses Victorian legislation from legislation.vic.gov.au that has been extracted
from PDF into text format.
"""

import logging
import re
from typing import Any

from mcp_fair_shake.models import (
    Act,
    Division,
    LegislationNode,
    Paragraph,
    Part,
    Section,
    Subsection,
)

log = logging.getLogger(__name__)


class VictorianTextParser:
    """Parser for Victorian legislation in structured text format."""

    def __init__(self) -> None:
        """Initialize parser with empty registry."""
        self.registry: dict[str, LegislationNode] = {}

    def can_parse(self, url: str, content_type: str) -> bool:
        """Check if this parser can handle the given URL and content type."""
        return "legislation.vic.gov.au" in url and "text" in content_type.lower()

    def parse(
        self, content: bytes, metadata: dict[str, Any]
    ) -> tuple[Act, dict[str, LegislationNode]]:
        """Parse Victorian legislation text into structured Act.

        Args:
            content: Text content of legislation (from PDF conversion)
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

        # Preprocess: Remove page markers and headers/footers
        text = self._preprocess_pdf_artifacts(text)

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

    def _preprocess_pdf_artifacts(self, text: str) -> str:
        """Remove PDF artifacts like page markers and headers/footers.

        Args:
            text: Raw text from PDF

        Returns:
            Cleaned text
        """
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Skip page markers: [Page 11]
            if re.match(r"^\[Page \d+\]$", line.strip()):
                continue

            # Skip header/footer lines
            if "Authorised by the Chief Parliamentary Counsel" in line:
                continue

            # Keep amendment notes (they start with "S. " or "Pt. ")
            # Keep all other lines
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

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
            # Skip empty lines
            if not line.strip():
                continue

            # Part marker: "Part 2—The Authority"
            # Note: May use em dash (— U+2014) or regular hyphen
            part_match = re.match(r"^Part ([\d\w]+)[—\-](.+)$", line.strip())
            if part_match:
                # Save previous section content
                if current_section and content_lines:
                    current_section.content = "\n".join(content_lines)
                    # Extract subsections and paragraphs
                    self._extract_subsections(current_section)
                    content_lines = []

                part_number, part_title = part_match.groups()
                part_id = f"{act.id}/part-{part_number}"

                # Only create part if it doesn't already exist (avoid duplicates from page headers)
                if part_id not in self.registry:
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
                else:
                    # Part already exists, just update current_part reference
                    current_part = self.registry[part_id]  # type: ignore

                current_division = None
                continue

            # Division marker: "Division 1—General functions and powers"
            div_match = re.match(r"^Division ([\d\w]+)[—\-](.+)$", line.strip())
            if div_match:
                # Save previous section content
                if current_section and content_lines:
                    current_section.content = "\n".join(content_lines)
                    # Extract subsections and paragraphs
                    self._extract_subsections(current_section)
                    content_lines = []

                div_number, div_title = div_match.groups()

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

            # Section marker: " 7 Functions of the Authority"
            # Note: Leading space, then number, then space, then title
            section_match = re.match(r"^\s+(\d+[A-Z]*)\s+(.+)$", line)
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
                    title=section_title.strip(),
                    content="",  # Will be populated
                    act_id=act.id,
                    section_number=section_number,
                    part_id=current_part.id if current_part else None,
                    division_id=current_division.id if current_division else None,
                    parent_id=(
                        current_division.id
                        if current_division
                        else current_part.id
                        if current_part
                        else act.id
                    ),
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

        Victorian legislation has hierarchy:
        - Subsection: (1), (2), etc.
        - Paragraph: (a), (b), etc.
        - Sub-paragraph: (i), (ii), etc. (roman numerals)

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
            stripped = line.strip()
            if not stripped:
                continue

            # Skip amendment notes (e.g., "S. 5(1) amended by...")
            if re.match(r"^S\.\s+\d+", stripped) or re.match(r"^Pt\.\s+\d+", stripped):
                continue

            # Subsection marker: " (1)" - space, paren-number-paren
            subsec_match = re.match(r"^\s+\((\d+[a-z]*)\)(.*)$", line)
            if subsec_match:
                # Save previous paragraph content
                if current_paragraph and content_lines:
                    current_paragraph.content += " " + " ".join(content_lines)
                    content_lines = []
                # Save previous subsection content
                elif current_subsection and content_lines:
                    current_subsection.content += " " + " ".join(content_lines)
                    content_lines = []

                subsec_number, subsec_content = subsec_match.groups()
                subsec_id = f"{section.id}/{subsec_number}"

                current_subsection = Subsection(
                    id=subsec_id,
                    title="",
                    content=subsec_content.strip(),  # Start with initial content
                    section_id=section.id,
                    subsection_number=subsec_number,
                    parent_id=section.id,
                )
                self.registry[subsec_id] = current_subsection
                section.subsections.append(subsec_id)
                section.children_ids.append(subsec_id)
                current_paragraph = None
                continue

            # Paragraph marker: " (a)" - space, paren-letter-paren
            # Note: Must NOT match roman numerals (i, ii, iii, etc.)
            para_match = re.match(
                r"^\s+\(([a-z]+)\)(.*)$", line
            )  # Only multi-char or single non-roman
            if para_match:
                para_letter = para_match.group(1)
                # Skip if it's a roman numeral (i, ii, iii, iv, v, vi, vii, viii, ix, x, etc.)
                if not self._is_roman_numeral(para_letter):
                    # Save collected content to previous paragraph or subsection
                    if current_paragraph and content_lines:
                        current_paragraph.content += " " + " ".join(content_lines)
                        content_lines = []
                    elif current_subsection and content_lines:
                        current_subsection.content += " " + " ".join(content_lines)
                        content_lines = []

                    para_content = para_match.group(2)

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
                        content=para_content.strip(),  # Start with initial content
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
            content_lines.append(stripped)

        # Save last item's collected content
        if current_paragraph and content_lines:
            current_paragraph.content += " " + " ".join(content_lines)
        elif current_subsection and content_lines:
            current_subsection.content += " " + " ".join(content_lines)

    def _is_roman_numeral(self, text: str) -> bool:
        """Check if text is a roman numeral (i, ii, iii, iv, v, vi, etc.).

        Args:
            text: Text to check

        Returns:
            True if text is a roman numeral, False otherwise
        """
        # Common roman numerals in legislation: i, ii, iii, iv, v, vi, vii, viii, ix, x
        # Pattern: only uses i, v, x characters
        return bool(re.match(r"^[ivx]+$", text.lower()))
