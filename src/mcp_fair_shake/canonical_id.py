"""Canonical ID parser and validator for Australian legislation.

Canonical ID Format: /{jurisdiction}/{code-type}/{code}/{section?}

Examples:
    /au-federal/fwa/2009/s394
    /au-victoria/ohs/2004/s21
    /au-federal/fwr/2009/reg3.01
"""

import re
from dataclasses import dataclass

VALID_JURISDICTIONS = {
    "au-federal",
    "au-victoria",
    "au-nsw",
    "au-queensland",
    "au-sa",
    "au-wa",
    "au-tasmania",
    "au-nt",
    "au-act",
}

VALID_CODE_TYPES = {
    "fwa": "Fair Work Act",
    "fwr": "Fair Work Regulations",
    "ma": "Modern Award",
    "ohs": "Occupational Health and Safety Act",
    "eoa": "Equal Opportunity Act",
    "lsl": "Long Service Leave Act",
    "wca": "Workers Compensation Act",
    "aca": "Accident Compensation Act",
}


@dataclass
class CanonicalID:
    """Parsed canonical ID for Australian legislation."""

    jurisdiction: str
    code_type: str
    year: str
    section: str | None = None

    @property
    def full_id(self) -> str:
        """Return the full canonical ID string."""
        base = f"/{self.jurisdiction}/{self.code_type}/{self.year}"
        if self.section:
            return f"{base}/{self.section}"
        return base

    @property
    def code_name(self) -> str:
        """Return the human-readable code name."""
        return VALID_CODE_TYPES.get(self.code_type, self.code_type.upper())

    @property
    def cache_filename(self) -> str:
        """Return the cache filename for this legislation.

        Format: {code_type}-{year}.txt
        Example: ohs-2004.txt
        """
        return f"{self.code_type}-{self.year}.txt"

    @property
    def metadata_filename(self) -> str:
        """Return the metadata filename for this legislation."""
        return f"{self.code_type}-{self.year}-metadata.json"

    @property
    def checksum_filename(self) -> str:
        """Return the checksum filename for this legislation."""
        return f"{self.code_type}-{self.year}.checksum"

    def __str__(self) -> str:
        """Return the full canonical ID."""
        return self.full_id


def parse_canonical_id(canonical_id: str) -> CanonicalID | None:
    """Parse a canonical ID string into components.

    Args:
        canonical_id: Canonical ID string (e.g., /au-victoria/ohs/2004/s21)

    Returns:
        CanonicalID object if valid, None otherwise

    Examples:
        >>> parse_canonical_id("/au-victoria/ohs/2004/s21")
        CanonicalID(jurisdiction='au-victoria', code_type='ohs', year='2004', section='s21')

        >>> parse_canonical_id("/au-federal/fwa/2009")
        CanonicalID(jurisdiction='au-federal', code_type='fwa', year='2009', section=None)
    """
    # Pattern: /{jurisdiction}/{code-type}/{year-or-code}/{section?}
    # Accepts 4-digit years (2009) or 6-digit codes (000004 for Modern Awards)
    pattern = r"^/([a-z-]+)/([a-z]+)/(\d{4,6})(?:/([a-z0-9.]+))?$"
    match = re.match(pattern, canonical_id.lower())

    if not match:
        return None

    jurisdiction, code_type, year, section = match.groups()

    # Validate jurisdiction
    if jurisdiction not in VALID_JURISDICTIONS:
        return None

    # Validate code type
    if code_type not in VALID_CODE_TYPES:
        return None

    return CanonicalID(
        jurisdiction=jurisdiction,
        code_type=code_type,
        year=year,
        section=section,
    )


def validate_canonical_id(canonical_id: str) -> bool:
    """Validate a canonical ID string.

    Args:
        canonical_id: Canonical ID string to validate

    Returns:
        True if valid, False otherwise
    """
    return parse_canonical_id(canonical_id) is not None


def build_canonical_id(
    jurisdiction: str,
    code_type: str,
    year: str,
    section: str | None = None,
) -> str:
    """Build a canonical ID from components.

    Args:
        jurisdiction: Jurisdiction (e.g., 'au-victoria')
        code_type: Code type (e.g., 'ohs')
        year: Year (e.g., '2004')
        section: Optional section (e.g., 's21')

    Returns:
        Canonical ID string

    Raises:
        ValueError: If jurisdiction or code_type is invalid
    """
    jurisdiction = jurisdiction.lower()
    code_type = code_type.lower()

    if jurisdiction not in VALID_JURISDICTIONS:
        raise ValueError(f"Invalid jurisdiction: {jurisdiction}")

    if code_type not in VALID_CODE_TYPES:
        raise ValueError(f"Invalid code type: {code_type}")

    base = f"/{jurisdiction}/{code_type}/{year}"
    if section:
        return f"{base}/{section}"
    return base
