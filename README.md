# mcp-fair-shake

> "Fair Shake of the Sauce Bottle" - Empowering employees with timely, grounded, and factual Australian workplace legislation

A Model Context Protocol (MCP) server providing **authoritative access to Australian workplace legislation**. Built with Python using **FastMCP**, following best practices from trusted MCPs like Context7, arXiv, and Sequential Thinking.

## What is MCP?

The [Model Context Protocol](https://modelcontextprotocol.io) is a standard way to connect AI assistants to external tools and data sources. This server implements MCP to provide Australian workplace legislation lookup to AI assistants like Claude Code and Claude Desktop.

## Project Status

**Phase 1 Complete** (December 2025):
- ✅ Three MCP tools: `resolve-legislation`, `get-legislation-content`, `get-cache-status`
- ✅ Local-first caching with SHA256 integrity verification
- ✅ CLI admin mode for cache management
- ✅ 83.54% test coverage with 61 passing tests
- ✅ Support for P0 legislation (Fair Work Act 2009, Victorian OHS Act 2004, Victorian Equal Opportunity Act 2010)

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

#### `resolve-legislation`

Resolve natural language queries or citations to canonical legislation IDs.

**Parameters:**
- `query` (string, required): Natural language query or citation (e.g., "unfair dismissal", "OHS Act s.21")
- `jurisdiction` (string, optional): Filter by jurisdiction (e.g., "au-victoria", "au-federal")

**Example:**
```json
{
  "query": "unfair dismissal",
  "jurisdiction": "au-federal"
}
```

**Returns:** Ranked matches with canonical IDs, titles, and cache status.

#### `get-legislation-content`

Retrieve legislation content from cache or download if needed.

**Parameters:**
- `canonical_id` (string, required): Canonical legislation ID (e.g., "/au-victoria/ohs/2004")
- `mode` (string, optional): Content mode - "text" (default, only mode in Phase 1)
- `section` (string, optional): Optional section filter (e.g., "s21")

**Example:**
```json
{
  "canonical_id": "/au-victoria/ohs/2004",
  "mode": "text",
  "section": "s21"
}
```

**Returns:** Legislation content with metadata.

#### `get-cache-status`

Get cache coverage, size, and missing items.

**Parameters:** None

**Returns:** JSON with cache statistics including P0 coverage, total size, and cached items.

### CLI Admin Mode

Pre-cache legislation and manage the cache:

```bash
# Check cache status
mcp-fair-shake status

# Pre-cache P0 legislation (MVP)
mcp-fair-shake cache --priority P0

# Pre-cache all configured legislation
mcp-fair-shake cache --priority all

# Force re-download
mcp-fair-shake cache --priority P0 --force

# Verify cache integrity
mcp-fair-shake verify
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
├── src/mcp_fair_shake/       # Main package
│   ├── __init__.py            # Package exports
│   ├── server.py              # MCP server with three tools
│   ├── canonical_id.py        # Canonical ID parser/validator
│   ├── cache.py               # Cache manager with SHA256 verification
│   ├── fetcher.py             # Legislation fetcher with retry logic
│   └── cli.py                 # CLI admin mode
├── tests/                     # Test suite (61 tests, 83.54% coverage)
│   ├── conftest.py            # Pytest fixtures
│   ├── test_server.py         # Server initialization tests
│   ├── test_tools.py          # MCP tool integration tests
│   ├── test_canonical_id.py   # Canonical ID parsing tests
│   ├── test_cache.py          # Cache management tests
│   └── test_fetcher.py        # Legislation fetcher tests
├── data/                      # Local legislation cache
│   ├── legislation/cache/     # Cached legislation files
│   ├── legislation/summaries/ # Plain language summaries (Phase 2+)
│   ├── legislation/parquet/   # Compressed queryable format (Phase 2+)
│   ├── support-pathways/      # Support agency databases (Phase 3+)
│   └── metadata/              # Cache index and logs
├── docs/                      # Documentation
│   ├── ROADMAP.md             # Implementation roadmap
│   ├── REQUIREMENTS.md        # Functional requirements
│   └── SPECIFICATION.md       # Technical specifications
├── pyproject.toml             # Project metadata and dependencies
├── Makefile                   # Development commands
└── README.md                  # This file
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
