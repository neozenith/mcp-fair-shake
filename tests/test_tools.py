"""Tests for MCP Fair Shake tools."""

from typing import Any

import pytest
from fastmcp.client import Client
from fastmcp.exceptions import ToolError


@pytest.mark.asyncio
async def test_evaluate_tool_basic(client: Client[Any]) -> None:
    """Test the evaluate tool with basic inputs."""
    result = await client.call_tool(
        "evaluate",
        arguments={"subject": "Python code", "criteria": "readability"},
    )

    assert result is not None
    assert result.data is not None
    assert "Python code" in result.data
    assert "readability" in result.data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("subject", "criteria"),
    [
        ("API design", "RESTful principles"),
        ("Database schema", "normalization"),
        ("User interface", "accessibility"),
        ("Algorithm", "time complexity"),
    ],
)
async def test_evaluate_tool_parametrized(client: Client[Any], subject: str, criteria: str) -> None:
    """Test the evaluate tool with various inputs."""
    result = await client.call_tool(
        "evaluate",
        arguments={"subject": subject, "criteria": criteria},
    )

    assert result is not None
    assert result.data is not None
    assert subject in result.data
    assert criteria in result.data


@pytest.mark.asyncio
async def test_evaluate_tool_missing_subject(client: Client[Any]) -> None:
    """Test the evaluate tool with missing subject."""
    # FastMCP validates required parameters and raises ToolError
    with pytest.raises(ToolError, match="Missing required argument"):
        await client.call_tool("evaluate", arguments={"criteria": "quality"})


@pytest.mark.asyncio
async def test_evaluate_tool_missing_criteria(client: Client[Any]) -> None:
    """Test the evaluate tool with missing criteria."""
    # FastMCP validates required parameters and raises ToolError
    with pytest.raises(ToolError, match="Missing required argument"):
        await client.call_tool("evaluate", arguments={"subject": "test"})


@pytest.mark.asyncio
async def test_evaluate_tool_empty_inputs(client: Client[Any]) -> None:
    """Test the evaluate tool with empty inputs."""
    result = await client.call_tool(
        "evaluate",
        arguments={"subject": "", "criteria": ""},
    )

    assert result is not None
    assert result.data is not None
    assert "error" in result.data.lower() or "required" in result.data.lower()


@pytest.mark.asyncio
async def test_unknown_tool(client: Client[Any]) -> None:
    """Test calling an unknown tool.

    FastMCP raises a clear exception for unknown tools, which is proper
    "fail loudly" behavior.
    """
    with pytest.raises(Exception, match="Unknown tool"):
        await client.call_tool("nonexistent_tool", arguments={})
