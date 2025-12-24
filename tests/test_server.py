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
    assert (
        len(tools) == 4
    )  # resolve_legislation, get_legislation_content, get_cache_status, get_support

    # Check that the legislation tools are present
    tool_names = [tool.name for tool in tools]
    assert "resolve_legislation" in tool_names
    assert "get_legislation_content" in tool_names
    assert "get_cache_status" in tool_names
    assert "get_support" in tool_names

    # Find and validate the resolve_legislation tool
    resolve_tool = next(tool for tool in tools if tool.name == "resolve_legislation")
    assert resolve_tool.description is not None
    assert "resolve" in resolve_tool.description.lower()
    assert resolve_tool.inputSchema is not None
    assert "properties" in resolve_tool.inputSchema
    assert "query" in resolve_tool.inputSchema["properties"]


@pytest.mark.asyncio
async def test_tool_call_basic(client: Client[Any]) -> None:
    """Test that the server can execute tool calls."""
    # Test that we can call resolve_legislation successfully
    result = await client.call_tool(
        "resolve_legislation",
        arguments={"query": "fair work"},
    )
    assert result is not None
    assert result.data is not None
    assert "matches" in result.data
