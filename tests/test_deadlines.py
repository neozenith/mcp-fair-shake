"""Tests for deadline tracking."""

from datetime import date, timedelta

from mcp_fair_shake.deadlines import (
    calculate_deadline,
    check_multiple_deadlines,
    format_deadline_warning,
    get_deadline_advice,
    parse_timeframe,
)


class TestParseTimeframe:
    """Test timeframe parsing."""

    def test_parse_days(self) -> None:
        """Test parsing day-based timeframes."""
        result = parse_timeframe("21 days from dismissal")
        assert result is not None
        assert result == (21, "dismissal")

    def test_parse_weeks(self) -> None:
        """Test parsing week-based timeframes."""
        result = parse_timeframe("2 weeks from adverse action")
        assert result is not None
        assert result == (14, "adverse action")

    def test_parse_months(self) -> None:
        """Test parsing month-based timeframes."""
        result = parse_timeframe("12 months from the discriminatory act")
        assert result is not None
        assert result == (360, "the discriminatory act")

    def test_parse_invalid(self) -> None:
        """Test parsing invalid timeframe."""
        result = parse_timeframe("invalid timeframe")
        assert result is None

    def test_parse_alternate_wording(self) -> None:
        """Test parsing with 'after' instead of 'from'."""
        result = parse_timeframe("21 days after dismissal")
        assert result is not None
        assert result == (21, "dismissal")


class TestCalculateDeadline:
    """Test deadline calculation."""

    def test_calculate_basic_deadline(self) -> None:
        """Test basic deadline calculation."""
        ref_date = date(2024, 1, 1)
        deadline = calculate_deadline("21 days from dismissal", ref_date)

        assert deadline is not None
        assert deadline.deadline_date == date(2024, 1, 22)
        assert deadline.reference_date == ref_date
        assert deadline.description == "21 days from dismissal"

    def test_urgency_critical(self) -> None:
        """Test critical urgency (7 days or less)."""
        # Set reference date so deadline is in 5 days
        ref_date = date.today() - timedelta(days=16)
        deadline = calculate_deadline("21 days from dismissal", ref_date)

        assert deadline is not None
        assert deadline.urgency == "critical"

    def test_urgency_urgent(self) -> None:
        """Test urgent urgency (8-14 days)."""
        # Set reference date so deadline is in 10 days
        ref_date = date.today() - timedelta(days=11)
        deadline = calculate_deadline("21 days from dismissal", ref_date)

        assert deadline is not None
        assert deadline.urgency == "urgent"

    def test_urgency_moderate(self) -> None:
        """Test moderate urgency (15-30 days)."""
        # Set reference date so deadline is in 20 days
        ref_date = date.today() - timedelta(days=1)
        deadline = calculate_deadline("21 days from dismissal", ref_date)

        assert deadline is not None
        assert deadline.urgency == "moderate"

    def test_urgency_low(self) -> None:
        """Test low urgency (>30 days)."""
        # Set reference date so deadline is in 60 days
        ref_date = date.today() + timedelta(days=30)
        deadline = calculate_deadline("90 days from event", ref_date)

        assert deadline is not None
        assert deadline.urgency == "low"

    def test_deadline_passed(self) -> None:
        """Test deadline that has already passed."""
        ref_date = date.today() - timedelta(days=30)
        deadline = calculate_deadline("21 days from dismissal", ref_date)

        assert deadline is not None
        assert deadline.days_remaining < 0
        assert deadline.urgency == "critical"

    def test_with_agency(self) -> None:
        """Test deadline calculation with agency name."""
        deadline = calculate_deadline(
            "21 days from dismissal",
            date.today(),
            agency="Fair Work Commission",
        )

        assert deadline is not None
        assert deadline.agency == "Fair Work Commission"

    def test_default_reference_date(self) -> None:
        """Test that reference date defaults to today."""
        deadline = calculate_deadline("21 days from dismissal")

        assert deadline is not None
        assert deadline.reference_date == date.today()


class TestCheckMultipleDeadlines:
    """Test checking multiple deadlines."""

    def test_multiple_deadlines(self) -> None:
        """Test checking multiple deadlines at once."""
        timeframes = {
            "unfair_dismissal": "21 days from dismissal",
            "general_protections": "21 days from adverse action",
        }

        ref_dates = {
            "unfair_dismissal": date.today() - timedelta(days=10),
            "general_protections": date.today() - timedelta(days=5),
        }

        deadlines = check_multiple_deadlines(timeframes, ref_dates, "Fair Work Commission")

        assert len(deadlines) == 2
        assert all(d.agency == "Fair Work Commission" for d in deadlines)

        # Should be sorted by urgency
        # The one with 5 days already passed is more urgent
        assert deadlines[0].days_remaining <= deadlines[1].days_remaining

    def test_empty_timeframes(self) -> None:
        """Test with no timeframes."""
        deadlines = check_multiple_deadlines({})
        assert len(deadlines) == 0

    def test_no_reference_dates(self) -> None:
        """Test without providing reference dates."""
        timeframes = {"unfair_dismissal": "21 days from dismissal"}

        deadlines = check_multiple_deadlines(timeframes)

        assert len(deadlines) == 1
        assert deadlines[0].reference_date == date.today()


class TestFormatDeadlineWarning:
    """Test deadline warning formatting."""

    def test_format_critical(self) -> None:
        """Test formatting critical deadline."""
        from mcp_fair_shake.deadlines import Deadline

        deadline = Deadline(
            description="21 days from dismissal",
            deadline_date=date(2024, 1, 22),
            days_remaining=5,
            reference_date=date(2024, 1, 1),
            urgency="critical",
        )

        warning = format_deadline_warning(deadline)
        assert "CRITICAL" in warning
        assert "5 days" in warning
        assert "2024-01-22" in warning

    def test_format_passed_deadline(self) -> None:
        """Test formatting passed deadline."""
        from mcp_fair_shake.deadlines import Deadline

        deadline = Deadline(
            description="21 days from dismissal",
            deadline_date=date(2024, 1, 22),
            days_remaining=-5,
            reference_date=date(2024, 1, 1),
            urgency="critical",
        )

        warning = format_deadline_warning(deadline)
        assert "DEADLINE PASSED" in warning
        assert "2024-01-22" in warning

    def test_format_one_day_remaining(self) -> None:
        """Test formatting with exactly 1 day remaining."""
        from mcp_fair_shake.deadlines import Deadline

        deadline = Deadline(
            description="21 days from dismissal",
            deadline_date=date.today() + timedelta(days=1),
            days_remaining=1,
            reference_date=date.today() - timedelta(days=20),
            urgency="critical",
        )

        warning = format_deadline_warning(deadline)
        assert "1 day remaining" in warning
        assert "1 days remaining" not in warning  # Check singular form


class TestGetDeadlineAdvice:
    """Test deadline advice generation."""

    def test_critical_advice(self) -> None:
        """Test advice for critical urgency."""
        advice = get_deadline_advice("critical")
        assert "immediately" in advice.lower()

    def test_urgent_advice(self) -> None:
        """Test advice for urgent urgency."""
        advice = get_deadline_advice("urgent")
        assert "soon" in advice.lower()

    def test_moderate_advice(self) -> None:
        """Test advice for moderate urgency."""
        advice = get_deadline_advice("moderate")
        assert len(advice) > 0

    def test_low_advice(self) -> None:
        """Test advice for low urgency."""
        advice = get_deadline_advice("low")
        assert len(advice) > 0
