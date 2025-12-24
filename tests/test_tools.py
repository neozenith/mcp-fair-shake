"""Tests for MCP Fair Shake tools."""

import json
from typing import Any

import pytest
from fastmcp.client import Client


@pytest.mark.asyncio
async def test_resolve_legislation_unfair_dismissal(client: Client[Any]) -> None:
    """Test resolving 'unfair dismissal' query."""
    result = await client.call_tool(
        "resolve_legislation",
        arguments={"query": "unfair dismissal"},
    )

    assert result is not None
    assert result.data is not None

    data = json.loads(result.data)
    assert "matches" in data
    assert data["total"] > 0

    # Should match Fair Work Act
    matches = data["matches"]
    assert any("Fair Work Act" in m["title"] for m in matches)


@pytest.mark.asyncio
async def test_resolve_legislation_ohs(client: Client[Any]) -> None:
    """Test resolving 'OHS' query."""
    result = await client.call_tool(
        "resolve_legislation",
        arguments={"query": "ohs"},
    )

    assert result is not None
    assert result.data is not None

    data = json.loads(result.data)
    assert "matches" in data
    assert data["total"] > 0

    # Should match OHS Act
    matches = data["matches"]
    assert any("Occupational Health" in m["title"] for m in matches)


@pytest.mark.asyncio
async def test_resolve_legislation_with_jurisdiction_filter(client: Client[Any]) -> None:
    """Test resolving with jurisdiction filter."""
    result = await client.call_tool(
        "resolve_legislation",
        arguments={"query": "equal opportunity", "jurisdiction": "au-victoria"},
    )

    assert result is not None
    assert result.data is not None

    data = json.loads(result.data)
    assert "matches" in data

    # All matches should be Victorian
    for match in data["matches"]:
        assert match["jurisdiction"] == "au-victoria"


@pytest.mark.asyncio
async def test_resolve_legislation_empty_query(client: Client[Any]) -> None:
    """Test resolve with empty query."""
    result = await client.call_tool(
        "resolve_legislation",
        arguments={"query": ""},
    )

    assert result is not None
    assert result.data is not None

    data = json.loads(result.data)
    assert "error" in data


@pytest.mark.asyncio
async def test_get_cache_status(client: Client[Any]) -> None:
    """Test getting cache status."""
    result = await client.call_tool("get_cache_status", arguments={})

    assert result is not None
    assert result.data is not None

    data = json.loads(result.data)
    assert "total_cached" in data
    assert "cache_size_mb" in data
    assert "p0_coverage" in data
    assert "supported_legislation" in data


@pytest.mark.asyncio
async def test_get_legislation_content_invalid_id(client: Client[Any]) -> None:
    """Test getting content with invalid canonical ID."""
    result = await client.call_tool(
        "get_legislation_content",
        arguments={"canonical_id": "/invalid/id"},
    )

    assert result is not None
    assert result.data is not None

    data = json.loads(result.data)
    assert "error" in data


@pytest.mark.asyncio
async def test_get_legislation_content_summary_mode(client: Client[Any]) -> None:
    """Test getting content with summary mode (Phase 2 feature)."""
    result = await client.call_tool(
        "get_legislation_content",
        arguments={"canonical_id": "/au-victoria/ohs/2004", "mode": "summary"},
    )

    assert result is not None
    assert result.data is not None

    # Summary mode should return either a summary or an error saying no summary available
    data = json.loads(result.data)
    assert "error" in data or "summary" in data


@pytest.mark.asyncio
async def test_get_legislation_content_metadata_mode(client: Client[Any]) -> None:
    """Test getting content with metadata mode (Phase 2 feature)."""
    result = await client.call_tool(
        "get_legislation_content",
        arguments={"canonical_id": "/au-victoria/ohs/2004", "mode": "metadata"},
    )

    assert result is not None
    assert result.data is not None

    # Metadata mode should return either metadata or an error saying no metadata available
    data = json.loads(result.data)
    assert "error" in data or "metadata" in data


@pytest.mark.asyncio
async def test_unknown_tool(client: Client[Any]) -> None:
    """Test calling an unknown tool.

    FastMCP raises a clear exception for unknown tools, which is proper
    "fail loudly" behavior.
    """
    with pytest.raises(Exception, match="Unknown tool"):
        await client.call_tool("nonexistent_tool", arguments={})


@pytest.mark.asyncio
async def test_get_support_unfair_dismissal(client: Client[Any]) -> None:
    """Test get-support for unfair dismissal scenario."""
    result = await client.call_tool(
        "get_support",
        arguments={"scenario": "unfair dismissal"},
    )

    assert result is not None
    assert result.data is not None

    data = json.loads(result.data)
    assert "matched_agencies" in data
    assert data["total_agencies"] > 0

    # Should match Fair Work Commission
    agencies = data["matched_agencies"]
    assert any("Fair Work Commission" in agency["name"] for agency in agencies)

    # Should have pathways
    assert "pathways" in data
    assert len(data["pathways"]) > 0

    # Check for critical deadlines
    assert "critical_deadlines" in data
    pathways = data["pathways"]
    # Unfair dismissal pathway should mention 21 day deadline
    assert any("21 day" in str(pathway) for pathway in pathways)


@pytest.mark.asyncio
async def test_get_support_wage_theft(client: Client[Any]) -> None:
    """Test get-support for wage theft scenario."""
    result = await client.call_tool(
        "get_support",
        arguments={"scenario": "wage theft"},
    )

    assert result is not None
    assert result.data is not None

    data = json.loads(result.data)
    assert "matched_agencies" in data
    assert data["total_agencies"] > 0

    # Should match Fair Work Ombudsman
    agencies = data["matched_agencies"]
    assert any("Fair Work Ombudsman" in agency["name"] for agency in agencies)


@pytest.mark.asyncio
async def test_get_support_discrimination(client: Client[Any]) -> None:
    """Test get-support for discrimination scenario."""
    result = await client.call_tool(
        "get_support",
        arguments={"scenario": "workplace discrimination"},
    )

    assert result is not None
    assert result.data is not None

    data = json.loads(result.data)
    assert "matched_agencies" in data

    # Should have discrimination pathway
    assert "pathways" in data


@pytest.mark.asyncio
async def test_get_support_with_jurisdiction_filter(client: Client[Any]) -> None:
    """Test get-support with jurisdiction filter."""
    result = await client.call_tool(
        "get_support",
        arguments={"scenario": "workplace safety", "jurisdiction": "victoria"},
    )

    assert result is not None
    assert result.data is not None

    data = json.loads(result.data)
    assert "matched_agencies" in data

    # All matched agencies should be Victorian or national
    for agency in data["matched_agencies"]:
        jurisdiction = agency.get("jurisdiction")
        assert jurisdiction in ["victoria", "national"]


@pytest.mark.asyncio
async def test_get_support_empty_scenario(client: Client[Any]) -> None:
    """Test get-support with empty scenario."""
    result = await client.call_tool(
        "get_support",
        arguments={"scenario": ""},
    )

    assert result is not None
    assert result.data is not None

    data = json.loads(result.data)
    assert "error" in data
    assert data["error"] == "Scenario is required"


@pytest.mark.asyncio
async def test_get_support_includes_contact_info(client: Client[Any]) -> None:
    """Test that get-support includes agency contact information."""
    result = await client.call_tool(
        "get_support",
        arguments={"scenario": "unfair dismissal"},
    )

    assert result is not None
    assert result.data is not None

    data = json.loads(result.data)
    agencies = data["matched_agencies"]

    # Check first agency has contact info
    if len(agencies) > 0:
        agency = agencies[0]
        assert "phone" in agency
        assert "website" in agency
        assert "description" in agency
        assert "eligibility" in agency
        assert "cost" in agency
