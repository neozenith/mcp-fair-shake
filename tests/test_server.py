"""Tests for the MCP Fair Shake server."""

from typing import Any

import pytest
from fastmcp.client import Client


@pytest.mark.asyncio
async def test_server_initialization(client: Client[Any]) -> None:
    """Test that the server initializes correctly."""
    # The fixture initialization already tests connection
    assert client is not None


@pytest.mark.asyncio
async def test_list_tools(client: Client[Any]) -> None:
    """Test that the server lists available tools."""
    tools = await client.list_tools()

    assert tools is not None
    assert len(tools) > 0

    # Check that the evaluate tool is present
    tool_names = [tool.name for tool in tools]
    assert "evaluate" in tool_names

    # Find and validate the evaluate tool
    evaluate_tool = next(tool for tool in tools if tool.name == "evaluate")
    assert evaluate_tool.description is not None
    assert "evaluate" in evaluate_tool.description.lower()
    assert evaluate_tool.inputSchema is not None
    assert "properties" in evaluate_tool.inputSchema
    assert "subject" in evaluate_tool.inputSchema["properties"]
    assert "criteria" in evaluate_tool.inputSchema["properties"]


@pytest.mark.asyncio
async def test_tool_call_basic(client: Client[Any]) -> None:
    """Test that the server can execute tool calls."""
    # Test that we can call a tool successfully
    result = await client.call_tool(
        "evaluate",
        arguments={"subject": "test", "criteria": "basic functionality"},
    )
    assert result is not None
    assert result.data is not None
    assert "test" in result.data
    assert "basic functionality" in result.data
