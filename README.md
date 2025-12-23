# mcp-fair-shake

> "Fair Shake of the Sauce Bottle"

A Model Context Protocol (MCP) server for fair evaluation and assessment. Built with Python using **FastMCP**, following best practices from trusted MCPs like SerenaMCP, Sequential Thinking MCP, Context7 MCP, and Playwright MCP.

## What is MCP?

The [Model Context Protocol](https://modelcontextprotocol.io) is a standard way to connect AI assistants to external tools and data sources. This server implements MCP to provide evaluation and assessment capabilities to AI assistants like Claude Code and Claude Desktop.

## Installation

### From GitHub (Recommended)

Install and run directly from the GitHub repository using `uvx`:

```bash
uvx --from git+https://github.com/neozenith/mcp-fair-shake mcp-fair-shake
```

### Local Development

Clone the repository and set up for development:

```bash
git clone https://github.com/neozenith/mcp-fair-shake.git
cd mcp-fair-shake
make init  # Installs dependencies and sets up the environment
```

## Usage

### Running the Server

The MCP server runs via stdio (standard input/output) for communication with MCP clients:

```bash
# Using uvx
uvx --from git+https://github.com/neozenith/mcp-fair-shake mcp-fair-shake

# Local development
uv run mcp-fair-shake
```

### Integrating with Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "mcp-fair-shake": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/neozenith/mcp-fair-shake",
        "mcp-fair-shake"
      ]
    }
  }
}
```

For local development:

```json
{
  "mcpServers": {
    "mcp-fair-shake": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-fair-shake",
        "run",
        "mcp-fair-shake"
      ]
    }
  }
}
```

### Available Tools

#### `evaluate`

Evaluate and provide a fair assessment of something.

**Parameters:**
- `subject` (string, required): The subject to evaluate
- `criteria` (string, required): The criteria to evaluate against

**Example:**
```json
{
  "subject": "Python code implementation",
  "criteria": "readability and maintainability"
}
```

## Development

### Setup

```bash
make init     # Initialize project and dependencies
make check    # Run all quality checks (format, lint, type check, tests)
make fix      # Auto-fix formatting and linting issues
```

### Testing

The project uses pytest with comprehensive test coverage:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Run specific test file
uv run pytest tests/test_server.py

# Run specific test
uv run pytest tests/test_tools.py::test_evaluate_tool_basic -v
```

**Testing Architecture:**
- Uses FastMCP's in-memory testing client for clean, fast tests
- Zero subprocess overhead or async teardown issues
- Tests verify tool registration, parameter validation, and responses
- Parametrized tests cover multiple scenarios
- All tests pass cleanly with no errors or warnings

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Type check
uv run mypy .

# All quality checks
make check
```

### Project Structure

```
mcp-fair-shake/
├── src/mcp_fair_shake/    # Main package
│   ├── __init__.py         # Package exports
│   └── server.py           # MCP server implementation
├── tests/                  # Test suite
│   ├── conftest.py         # Pytest fixtures
│   ├── test_server.py      # Server tests
│   └── test_tools.py       # Tool tests
├── pyproject.toml          # Project metadata and dependencies
├── Makefile                # Development commands
└── README.md               # This file
```

## Architecture

This MCP server is built using:

- **Python 3.12+**: Modern Python with type hints
- **FastMCP 0.3+**: Fast, Pythonic way to build MCP servers with clean testing
- **pytest**: Testing with async support via pytest-asyncio
- **ruff**: Fast linting and formatting
- **mypy**: Static type checking
- **uv**: Fast Python package management

## Best Practices from Trusted MCPs

This project follows patterns from leading MCP implementations:

- **SerenaMCP**: AsyncIO-based architecture, support for stdio/HTTP/SSE transports
- **Sequential Thinking MCP**: Comprehensive pytest test suite with test_*.py organization
- **Context7 MCP**: Clear tool definition with inputSchema validation, uvx installation patterns
- **Playwright MCP**: Security-first approach, subprocess isolation, pinned dependencies
- **FastMCP**: Clean API with decorators, in-memory testing, "fail loudly" error handling

## Contributing

Contributions are welcome! This project follows pragmatic development principles:

1. **Working code first** - Shipped code with minor issues > perfect code that never ships
2. **YAGNI** - Don't build abstractions until they're proven necessary
3. **Testing when needed** - Create tests when complexity requires it
4. **Quality standards** - All code must pass ruff, mypy, and existing tests

## License

MIT License - see LICENSE file for details

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [FastMCP Testing Patterns](https://gofastmcp.com/patterns/testing)
- [Testing MCP Servers Guide](https://mcpcat.io/guides/writing-unit-tests-mcp-servers/)
