# mcp-fair-shake

## Etymology

> ["**Fair Shake** of the Sauce Bottle mate"](https://slll.cass.anu.edu.au/centres/andc/meanings-origins/f#:~:text=fair%20shake)
>
> -- Kevin Rudd, 2006

## Mission

> _Empowering employees with timely, grounded, and factual Australian workplace legislation and support pathways._

## The How

A Model Context Protocol (MCP) server providing **authoritative access to Australian workplace legislation**. Built with Python using **FastMCP**, following best practices from trusted MCPs like Context7, arXiv, and Sequential Thinking.

### What is MCP?

The [Model Context Protocol](https://modelcontextprotocol.io) is a standard way to connect AI assistants to external tools and data sources. This server implements MCP to provide Australian workplace legislation lookup to AI assistants like Claude Code and Claude Desktop.

## Project Status

### ✅ Completed Phases (4/10 complete)

#### Phase 1: Core Infrastructure
- MCP tools: `resolve-legislation`, `get-legislation-content`, `get-cache-status`
- Local-first caching with SHA256 integrity verification
- CLI admin mode for cache management and pre-caching

#### Phase 2.5: Fine-Grained Extraction
- Pydantic models for hierarchical legislation structure (Act → Part → Division → Section → Subsection → Paragraph)
- Federal and Victorian text parsers with state machine parsing
- **11,882 nodes extracted** across 8 Acts (365x more granular than manual graph)
- D3.js force-directed graph visualization with hierarchical relationships

#### Phase 3: Support Pathways
- `get-support` tool for employee support agency lookup
- Deadline tracking with urgency indicators (21 days for unfair dismissal)
- Victorian and federal support pathways (Fair Work Commission, WorkSafe Victoria, etc.)

#### Phase 4: Federal Coverage
- Fair Work Act 2009, Fair Work Regulations 2009
- Top 10 Modern Awards by employee coverage
- Federal/state jurisdiction filtering

### 📍 Remaining Phases (6/10)

#### Phase 5: Hierarchical Summaries
Recursive bottom-up summarization of legislation graph (map tile pyramid pattern: leaf nodes → parents → root)

#### Phase 6: Advanced Data & Search
- Phase 6.1: DuckDB integration for efficient querying
- Phase 6.2: Leaf node embeddings + TF-IDF for content-based search
- Phase 6.3: Node2Vec embeddings + DRIFT hierarchical knowledge graph algorithm
- Phase 6.4: Advanced search/filter UI

#### Phase 7: Conversational Breach Test Cases Generator
- 100% compliant scenarios: Surface legislation, interpret as "No Non-Compliance detected"
- 0% compliant scenarios: Blatant breaches surface legislation with "Non-compliance potentially detected"
- 50% compliant scenarios: Boundary cases that test interpretation edge cases

#### Phase 8: Live Audio Transcription
Google ADK live streaming APIs with Gemini integration for real-time workplace conversation analysis

#### Phase 9: GitHub Pages WebApp
Interactive legislation exploration interface deployed via GitHub Pages

#### Phase 10: National Coverage
All Australian states and territories (NSW, QLD, SA, WA, TAS, NT, ACT)

### Current Legislation Coverage
- **Federal:** Fair Work Act 2009, Fair Work Regulations 2009, 10 Modern Awards
- **Victorian:** OHS Act 2004, Equal Opportunity Act 2010, Long Service Leave Act 2018, Workers Compensation Act 1958, Accident Compensation Act 1985

### Testing & Quality
111 tests passing, 82.75% coverage, zero mocks, full type safety with mypy strict mode

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

Retrieve legislation content from cache or download if needed. Supports both HTML (federal) and PDF (Victorian, Modern Awards) sources.

**Parameters:**
- `canonical_id` (string, required): Canonical legislation ID
  - Federal Acts: `/au-federal/fwa/2009`
  - Modern Awards: `/au-federal/ma/000004`
  - Victorian Acts: `/au-victoria/ohs/2004`
- `mode` (string, optional): Content mode - "text", "summary", or "metadata"
- `section` (string, optional): Optional section filter (e.g., "s21")

**Example:**
```json
{
  "canonical_id": "/au-federal/ma/000004",
  "mode": "text"
}
```

**Returns:** Legislation content with metadata, including page markers for PDF sources.

#### `get-support`

Find support agencies and resolution pathways for workplace issues.

**Parameters:**
- `scenario` (string, required): Workplace issue description (e.g., "unfair dismissal", "wage theft", "discrimination")
- `jurisdiction` (string, optional): Filter by jurisdiction (e.g., "au-victoria", "au-federal")

**Example:**
```json
{
  "scenario": "unfair dismissal",
  "jurisdiction": "au-federal"
}
```

**Returns:** Support agencies, contact information, deadlines, and step-by-step guidance.

#### `get-cache-status`

Get cache coverage, size, and missing items.

**Parameters:** None

**Returns:** JSON with cache statistics including coverage, total size, and cached items.

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
- **NO MOCKS POLICY** - All tests use real HTTP requests and actual data
- Uses FastMCP's in-memory testing client for clean, fast tests
- Integration tests verify end-to-end functionality with real legislation sources
- PDF and HTML parsing tested with actual government documents
- Zero subprocess overhead or async teardown issues
- Parametrized tests cover multiple scenarios
- 111 tests, 82.75% coverage, all passing with no errors or warnings

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
├── tests/                     # Test suite (111 tests, 82.75% coverage)
│   ├── conftest.py            # Pytest fixtures
│   ├── test_server.py         # Server initialization tests
│   ├── test_tools.py          # MCP tool integration tests
│   ├── test_canonical_id.py   # Canonical ID parsing tests
│   ├── test_cache.py          # Cache management tests
│   ├── test_fetcher.py        # Legislation fetcher unit tests
│   ├── test_fetcher_integration.py  # Real HTTP integration tests (NO MOCKS)
│   ├── test_pdf_parser.py     # PDF parsing tests
│   ├── test_html_parser.py    # HTML parsing tests
│   ├── test_playwright_fetcher.py   # Playwright browser automation tests
│   └── test_deadlines.py      # Deadline tracking and urgency tests
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
