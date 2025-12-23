"""Pytest configuration and fixtures for MCP Fair Shake tests."""

from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastmcp.client import Client

from mcp_fair_shake import mcp


@pytest.fixture
async def client() -> AsyncIterator[Client[Any]]:
    """Create a FastMCP test client.

    This fixture provides an in-memory client connected directly to the server,
    eliminating subprocess overhead and async teardown issues.
    """
    async with Client(mcp) as client:
        yield client
