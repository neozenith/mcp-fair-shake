"""Tests for MCP Fair Shake tools."""

import json
from typing import Any

import pytest
from fastmcp.client import Client
from fastmcp.exceptions import ToolError


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
