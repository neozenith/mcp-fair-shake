"""Cross-reference parsing for Australian legislation.

Identifies and links citations to related legislation sections.
"""

import re
from dataclasses import dataclass


@dataclass
class CrossReference:
    """A cross-reference to another piece of legislation."""

    source_canonical_id: str
    target_canonical_id: str | None
    citation_text: str
    section: str | None
    confidence: float  # 0.0 to 1.0


# Citation patterns for Australian legislation
CITATION_PATTERNS = {
    # Section references within same Act
    "section": re.compile(
        r"(?:section|s\.|s\s)(\d+[A-Z]?(?:\(\d+\))?(?:\([a-z]\))?)",
        re.IGNORECASE,
    ),
    # References to other Acts
    "act_reference": re.compile(
        r"((?:Fair Work|Occupational Health and Safety|Equal Opportunity|"
        r"Long Service Leave|Workers Compensation|Accident Compensation)\s+Act\s+\d{4})",
        re.IGNORECASE,
    ),
    # Part references
    "part": re.compile(r"Part\s+(\d+[A-Z]?(?:-\d+)?)", re.IGNORECASE),
    # Division references
    "division": re.compile(r"Division\s+(\d+[A-Z]?)", re.IGNORECASE),
}

# Map Act names to canonical ID prefixes
ACT_NAME_TO_ID: dict[str, str] = {
    "fair work act 2009": "/au-federal/fwa/2009",
    "occupational health and safety act 2004": "/au-victoria/ohs/2004",
    "equal opportunity act 2010": "/au-victoria/eoa/2010",
    "long service leave act 2018": "/au-victoria/lsl/2018",
    "workers compensation act 1958": "/au-victoria/wca/1958",
    "accident compensation act 1985": "/au-victoria/aca/1985",
}


def parse_cross_references(content: str, source_canonical_id: str) -> list[CrossReference]:
    """Parse cross-references from legislation content.

    Args:
        content: Legislation text
        source_canonical_id: Canonical ID of the source legislation

    Returns:
        List of cross-references found
    """
    cross_refs = []

    # Find section references
    for match in CITATION_PATTERNS["section"].finditer(content):
        section = match.group(1)
        citation = match.group(0)

        # Section reference within same Act
        target_id = f"{source_canonical_id}/s{section}"

        cross_refs.append(
            CrossReference(
                source_canonical_id=source_canonical_id,
                target_canonical_id=target_id,
                citation_text=citation,
                section=section,
                confidence=0.9,  # High confidence for section refs
            )
        )

    # Find references to other Acts
    for match in CITATION_PATTERNS["act_reference"].finditer(content):
        act_name = match.group(1).lower()
        citation = match.group(0)

        # Try to map to canonical ID
        act_target_id: str | None = ACT_NAME_TO_ID.get(act_name)

        cross_refs.append(
            CrossReference(
                source_canonical_id=source_canonical_id,
                target_canonical_id=act_target_id,
                citation_text=citation,
                section=None,
                confidence=0.8 if act_target_id else 0.5,
            )
        )

    return cross_refs


def find_related_sections(canonical_id: str, content: str, max_results: int = 10) -> list[str]:
    """Find sections related to a given piece of legislation.

    Args:
        canonical_id: Canonical ID to find related sections for
        content: Legislation content to search
        max_results: Maximum number of results

    Returns:
        List of related canonical IDs
    """
    cross_refs = parse_cross_references(content, canonical_id)

    # Filter to high-confidence cross-references with targets
    related = [
        ref.target_canonical_id
        for ref in cross_refs
        if ref.target_canonical_id and ref.confidence >= 0.7
    ]

    # Remove duplicates and limit
    seen = set()
    unique_related = []
    for ref in related:
        if ref not in seen:
            seen.add(ref)
            unique_related.append(ref)
            if len(unique_related) >= max_results:
                break

    return unique_related


def extract_section_number(section_text: str) -> str | None:
    """Extract section number from text.

    Args:
        section_text: Text containing section reference

    Returns:
        Section number or None
    """
    match = CITATION_PATTERNS["section"].search(section_text)
    if match:
        return match.group(1)
    return None


def build_cross_reference_index(
    legislation_content: dict[str, str],
) -> dict[str, list[CrossReference]]:
    """Build an index of all cross-references in multiple pieces of legislation.

    Args:
        legislation_content: Dict mapping canonical IDs to content

    Returns:
        Dict mapping canonical IDs to lists of cross-references
    """
    index = {}

    for canonical_id, content in legislation_content.items():
        cross_refs = parse_cross_references(content, canonical_id)
        index[canonical_id] = cross_refs

    return index


def get_citation_context(content: str, citation_text: str, context_lines: int = 2) -> str:
    """Get context around a citation.

    Args:
        content: Full legislation content
        citation_text: Citation text to find
        context_lines: Number of lines of context before and after

    Returns:
        Context string
    """
    lines = content.split("\n")

    for i, line in enumerate(lines):
        if citation_text in line:
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            context = lines[start:end]
            return "\n".join(context)

    return ""
