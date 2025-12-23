# Testing Guide for MCP Fair Shake

This document explains the testing approach for the MCP Fair Shake server and how to run tests effectively.

## Overview

The project uses **pytest** with **pytest-asyncio** for testing the MCP server. Tests use **FastMCP's in-memory testing client** which connects directly to the server without subprocess overhead, providing clean, fast, and reliable tests.

## Running Tests

### Quick Test Run

```bash
# Run all tests (without coverage)
make test

# Or directly with uv
uv run pytest -v --no-cov
```

### With Coverage

```bash
# Run tests with coverage report
make test-cov

# Or directly with uv
uv run pytest -v
```

### Run Specific Tests

```bash
# Run a specific test file
uv run pytest tests/test_server.py -v

# Run a specific test function
uv run pytest tests/test_tools.py::test_evaluate_tool_basic -v

# Run with specific markers or patterns
uv run pytest -k "evaluate" -v
```

## Test Architecture

### Fixtures (tests/conftest.py)

The `client` fixture creates a FastMCP test client with in-memory connection:

```python
@pytest.fixture
async def client() -> AsyncIterator[Client]:
    """Create a FastMCP test client.

    This fixture provides an in-memory client connected directly to the server,
    eliminating subprocess overhead and async teardown issues.
    """
    async with Client(mcp) as client:
        yield client
```

### Test Organization

- **tests/test_server.py**: Tests for server initialization and basic operations
- **tests/test_tools.py**: Tests for MCP tools (evaluate, etc.)
- **tests/conftest.py**: Shared fixtures and test configuration

### Test Patterns

1. **Server Initialization**: Verifies the server starts and responds
2. **Tool Registration**: Checks that tools are properly registered
3. **Tool Execution**: Tests tool calls with various inputs
4. **Parameter Validation**: Ensures required parameters are validated
5. **Error Handling**: Tests error cases and invalid inputs

## Why FastMCP?

FastMCP provides several advantages for testing:

- ✅ **Clean tests**: No subprocess management or teardown issues
- ✅ **Fast execution**: In-memory connection is much faster than subprocess
- ✅ **Clear errors**: Proper "fail loudly" behavior for unknown tools and missing parameters
- ✅ **Type safety**: Full type hints and mypy compliance
- ✅ **Simple API**: Clean decorators and intuitive client interface

All tests pass cleanly with **zero errors or warnings**, aligning with the project's "fail loudly and halt" philosophy.

## Test Coverage

The test suite covers:

- ✅ Server initialization and connection
- ✅ Tool discovery (list_tools)
- ✅ Tool execution with valid inputs
- ✅ Parameter validation and error handling
- ✅ Parametrized testing for multiple scenarios
- ✅ Unknown tool handling

## Best Practices for Testing MCPs

Based on research from trusted MCPs and FastMCP best practices:

1. **Use in-memory testing** for fast, reliable tests (FastMCP pattern)
2. **Parametrize tests** for comprehensive coverage
3. **Validate tool schemas** in tests
4. **Test error cases** explicitly with proper exception handling
5. **Avoid "vibe-testing"** with LLMs (use deterministic tests)
6. **Follow "fail loudly" principle** - tests should raise clear exceptions for errors

## Adding New Tests

When adding new tools, create tests following this pattern:

```python
@pytest.mark.asyncio
async def test_new_tool_basic(client: Client) -> None:
    """Test the new tool with basic inputs."""
    result = await client.call_tool(
        "new_tool_name",
        arguments={"param1": "value1", "param2": "value2"},
    )

    assert result is not None
    assert result.data is not None
    # Add specific assertions on result.data
```

Use parametrized tests for multiple scenarios:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("param1", "param2", "expected"),
    [
        ("value1", "value2", "expected1"),
        ("value3", "value4", "expected2"),
    ],
)
async def test_new_tool_parametrized(
    client: Client, param1: str, param2: str, expected: str
) -> None:
    """Test the new tool with various inputs."""
    result = await client.call_tool(
        "new_tool_name",
        arguments={"param1": param1, "param2": param2},
    )
    assert expected in result.data
```

## One-Off Claude Code Testing Setup

This section explains how to temporarily configure Claude Code to test this MCP **without permanently modifying your Claude Code configuration**. This is useful for testing changes during development while keeping your main Claude Code setup clean.

### Option 1: Using `make claude` (Recommended)

The simplest way to launch Claude Code with this MCP configured is using the Makefile target:

```bash
# Run all quality checks and launch Claude Code with MCP configured
make claude
```

This will:
1. ✅ Run `make init` - Sync dependencies
2. ✅ Run `make check` - Format, lint, and type check
3. ✅ Run `make test` - Run full test suite with 80% coverage enforcement
4. ✅ Launch Claude Code with `mcp-config.json` configured

The `mcp-config.json` is a permanent file checked into the repo that uses `"."` as the directory path, which Claude Code resolves relative to the config file location.

When you close Claude Code, the temporary configuration is not persisted - your permanent Claude Code settings remain unchanged.

### Option 2: Direct Claude Code Launch

If you want to skip the quality checks and launch Claude Code directly:

```bash
# Launch from the project directory
cd /path/to/mcp-fair-shake
claude-code --mcp-config $(pwd)/mcp-config.json
```

This uses the same `mcp-config.json` but skips running tests and quality checks.

### Option 3: Manual Configuration Toggle

If you need to test with Claude Desktop or permanently configure Claude Code:

**To Enable (for testing):**

1. Find your Claude Code configuration file:
   - **macOS**: `~/.config/claude-code/settings.json`
   - **Linux**: `~/.config/claude-code/settings.json`
   - **Windows**: `%APPDATA%\claude-code\settings.json`

2. Add the MCP server configuration to the `mcpServers` section:

```json
{
  "mcpServers": {
    "mcp-fair-shake": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-fair-shake/",
        "run",
        "mcp-fair-shake"
      ]
    }
  }
}
```

3. Restart Claude Code

**To Disable (after testing):**

1. Remove the `mcp-fair-shake` entry from `mcpServers`
2. Restart Claude Code

### Verifying the MCP Works

Once configured, test that the MCP is working:

1. **List available tools** in Claude Code:
   ```
   Can you list the available MCP tools?
   ```

2. **Test the evaluate tool**:
   ```
   Use the evaluate tool to assess "Python code readability" against "PEP 8 standards"
   ```

3. **Check MCP logs** (if issues occur):
   ```bash
   # The MCP server logs to stderr by default
   # You can run it directly to see logs:
   uv run mcp-fair-shake
   ```

### Best Practices for Testing

1. **Use `make claude`** as the primary testing method - it ensures all quality checks pass before launching
2. **Use temporary configurations** (like `--mcp-config`) to avoid polluting your permanent Claude Code setup
3. **Test in isolation** - close other Claude Code instances when testing to avoid confusion
4. **Check logs** if the MCP doesn't appear or behaves unexpectedly:
   ```bash
   uv run mcp-fair-shake
   ```
5. **Verify with pytest first** - if pytest tests fail, the MCP won't work correctly in Claude Code either

## References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [FastMCP Testing Patterns](https://gofastmcp.com/patterns/testing)
- [Testing MCP Servers Guide](https://mcpcat.io/guides/writing-unit-tests-mcp-servers/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
