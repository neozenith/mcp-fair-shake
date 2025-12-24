"""Deadline tracking for workplace claim timeframes.

Calculates deadlines and time remaining for critical workplace actions.
"""

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal


@dataclass
class Deadline:
    """A calculated deadline for a workplace claim or action."""

    description: str
    deadline_date: date
    days_remaining: int
    reference_date: date
    urgency: Literal["critical", "urgent", "moderate", "low"]
    agency: str | None = None


def parse_timeframe(timeframe_text: str) -> tuple[int, str] | None:
    """Parse a timeframe string into days and event type.

    Args:
        timeframe_text: Text like "21 days from dismissal" or
            "12 months from the discriminatory act"

    Returns:
        Tuple of (days, event_type) or None if not parseable

    Example:
        >>> parse_timeframe("21 days from dismissal")
        (21, "dismissal")
        >>> parse_timeframe("12 months from the discriminatory act")
        (365, "discriminatory act")
    """
    # Pattern: "{number} {unit} from {event}"
    pattern = r"(\d+)\s+(day|days|month|months|week|weeks)\s+(?:from|after)\s+(.+)"
    match = re.search(pattern, timeframe_text.lower())

    if not match:
        return None

    number = int(match.group(1))
    unit = match.group(2)
    event = match.group(3).strip()

    # Convert to days
    if "month" in unit:
        days = number * 30  # Approximate month as 30 days
    elif "week" in unit:
        days = number * 7
    else:  # days
        days = number

    return (days, event)


def calculate_deadline(
    timeframe_text: str,
    reference_date: date | None = None,
    agency: str | None = None,
) -> Deadline | None:
    """Calculate a deadline based on timeframe and reference date.

    Args:
        timeframe_text: Text like "21 days from dismissal"
        reference_date: Date of the triggering event (defaults to today)
        agency: Name of the agency this deadline applies to

    Returns:
        Deadline object or None if timeframe cannot be parsed

    Example:
        >>> calculate_deadline("21 days from dismissal", date(2024, 1, 1))
        Deadline(description="21 days from dismissal", deadline_date=date(2024, 1, 22), ...)
    """
    parsed = parse_timeframe(timeframe_text)
    if not parsed:
        return None

    days, event = parsed

    # Use provided reference date or default to today
    ref_date = reference_date or date.today()

    # Calculate deadline
    deadline_date = ref_date + timedelta(days=days)

    # Calculate days remaining
    today = date.today()
    days_remaining = (deadline_date - today).days

    # Determine urgency
    if days_remaining <= 0:
        urgency: Literal["critical", "urgent", "moderate", "low"] = "critical"
    elif days_remaining <= 7:
        urgency = "critical"
    elif days_remaining <= 14:
        urgency = "urgent"
    elif days_remaining <= 30:
        urgency = "moderate"
    else:
        urgency = "low"

    return Deadline(
        description=timeframe_text,
        deadline_date=deadline_date,
        days_remaining=days_remaining,
        reference_date=ref_date,
        urgency=urgency,
        agency=agency,
    )


def check_multiple_deadlines(
    timeframes: dict[str, str],
    reference_dates: dict[str, date] | None = None,
    agency: str | None = None,
) -> list[Deadline]:
    """Check multiple deadlines at once.

    Args:
        timeframes: Dict mapping event names to timeframe texts
        reference_dates: Optional dict mapping event names to reference dates
        agency: Name of the agency these deadlines apply to

    Returns:
        List of Deadline objects, sorted by urgency (most urgent first)

    Example:
        >>> check_multiple_deadlines({
        ...     "unfair_dismissal": "21 days from dismissal",
        ...     "general_protections": "21 days from adverse action"
        ... }, reference_dates={"unfair_dismissal": date(2024, 1, 1)})
        [Deadline(...), Deadline(...)]
    """
    deadlines = []
    ref_dates = reference_dates or {}

    for event_name, timeframe_text in timeframes.items():
        ref_date = ref_dates.get(event_name)
        deadline = calculate_deadline(timeframe_text, ref_date, agency)
        if deadline:
            deadlines.append(deadline)

    # Sort by urgency and days remaining
    urgency_order = {"critical": 0, "urgent": 1, "moderate": 2, "low": 3}
    deadlines.sort(key=lambda d: (urgency_order[d.urgency], d.days_remaining))

    return deadlines


def format_deadline_warning(deadline: Deadline) -> str:
    """Format a deadline as a human-readable warning.

    Args:
        deadline: Deadline to format

    Returns:
        Formatted warning string

    Example:
        >>> deadline = Deadline(
        ...     description="21 days from dismissal",
        ...     deadline_date=date(2024, 1, 22),
        ...     days_remaining=5,
        ...     reference_date=date(2024, 1, 1),
        ...     urgency="critical"
        ... )
        >>> format_deadline_warning(deadline)
        "⚠️ CRITICAL: Only 5 days remaining (deadline: 2024-01-22) for 21 days from dismissal"
    """
    if deadline.days_remaining <= 0:
        return f"❌ DEADLINE PASSED: {deadline.description} (was due {deadline.deadline_date})"

    urgency_emoji = {
        "critical": "⚠️",
        "urgent": "⏰",
        "moderate": "📅",
        "low": "ℹ️",
    }

    emoji = urgency_emoji.get(deadline.urgency, "ℹ️")
    urgency_text = deadline.urgency.upper()

    if deadline.days_remaining == 1:
        time_text = "Only 1 day remaining"
    else:
        time_text = f"Only {deadline.days_remaining} days remaining"

    return (
        f"{emoji} {urgency_text}: {time_text} "
        f"(deadline: {deadline.deadline_date}) for {deadline.description}"
    )


def get_deadline_advice(urgency: Literal["critical", "urgent", "moderate", "low"]) -> str:
    """Get actionable advice based on urgency level.

    Args:
        urgency: Urgency level

    Returns:
        Advice string

    Example:
        >>> get_deadline_advice("critical")
        "Act immediately - seek urgent legal advice if needed"
    """
    advice = {
        "critical": "Act immediately - seek urgent legal advice if needed",
        "urgent": "Act soon - prepare your documentation and contact the relevant agency",
        "moderate": "Start preparing - gather evidence and seek advice",
        "low": "Plan ahead - research your options and document the situation",
    }

    return advice.get(urgency, "Seek advice from a qualified professional")
