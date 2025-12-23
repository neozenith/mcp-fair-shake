# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mcp-fair-shake** is a Model Context Protocol (MCP) server built with **FastMCP** and Python 3.12+. The project uses `uv` for dependency management and follows a pragmatic, minimalist approach to development with an emphasis on working code over perfect code.

### Key Technologies

- **FastMCP**: Fast, Pythonic way to build MCP servers with clean testing
- **Python 3.12+**: Modern Python with full type hints
- **pytest**: Testing with **80% minimum coverage requirement** (currently 83.33%)
- **ruff**: Fast linting and formatting
- **mypy**: Strict static type checking
- **uv**: Fast Python package management

### MCP Server Architecture

The server provides tools via the Model Context Protocol for AI assistants like Claude Code and Claude Desktop.

**Current Tools:**
- `evaluate` - Fair assessment tool that evaluates a subject against criteria

## Development Commands

### Setup
```bash
# Initialize the project and dependencies
make init

# The init target will:
# - Install dependencies with uv sync --dev
# - Create .serena/project.yml for SerenaMCP integration
# - Index the project with SerenaMCP
```

### Testing
```bash
# Run tests (fast, without coverage)
make test

# Run tests with coverage (80% minimum required)
make test-cov

# Or directly with pytest
uv run pytest -v --no-cov    # Fast
uv run pytest -v              # With coverage
```

**Coverage Requirements:**
- **Minimum coverage: 80%** (enforced by pytest with `--cov-fail-under=80`)
- Current coverage: 83.33%
- Coverage reports: `htmlcov/index.html`

**Testing Standards:**
- ✅ `make test` must ALWAYS pass before committing
- ✅ `make check` must ALWAYS pass before merging
- ✅ All tests must be clean with zero errors or warnings
- ✅ FastMCP in-memory testing provides 60x faster tests than subprocess

### Code Quality
```bash
# Format and fix linting issues automatically
make fix

# Run comprehensive quality checks (format, lint, type check, tests with coverage, and index)
make check
```

**Quality Standards - MUST PASS:**
- ✅ `make test` - All 12 tests pass
- ✅ Coverage ≥ 80%
- ✅ `ruff format` - Code formatted consistently
- ✅ `ruff check` - No linting issues
- ✅ `mypy` - Full type safety in strict mode

### Manual Quality Tools
```bash
# Formatting
uv run ruff format .
uv run ruff check . --fix

# Type checking
uv run mypy .

# Documentation TOC generation
make docs
```

### Running the Project
```bash
# Run the main entry point
mcp-fair-shake

# Or using uv directly
uv run mcp-fair-shake
```

## Architecture & Design Principles

### Core Philosophy: Pragmatic Minimalism

This project emphasizes **pragmatism over perfection**. Key principles from `.claude/misc/PRINCIPLES.md`:

1. **Working Code First**: Shipped code with minor issues > perfect code that never ships
2. **YAGNI (You Aren't Gonna Need It)**: Don't build abstractions until they're proven necessary
3. **Stand-Alone Scripts**: Each script should be independently executable with minimal dependencies
4. **No Premature Refactoring**: Only refactor when:
   - Code causes actual failures or data issues
   - A problem has occurred in the last 6 months
   - The fix is simpler than the problem
   - Someone will notice if you don't fix it

### Testing Philosophy

**For MCP Server Code** (src/mcp_fair_shake/):
- ✅ **Tests Required** - 80% minimum coverage enforced
- ✅ Use FastMCP's in-memory testing for clean, fast tests
- ✅ Parametrized tests for comprehensive coverage
- ✅ All tests must pass with zero errors/warnings
- ✅ Tests verify tool behavior, parameter validation, error handling

**For Helper Scripts** (scripts/):
- **Default: No Tests** - If a script works on first run, execution IS the test
- **Create Tests When**:
  - A script fails after your first fix attempt (signals complexity)
  - Tests are explicitly requested
  - Target >50% coverage (pragmatic) or >75% (ideal)
  - Use parametrized tests to maximize coverage with minimal code

### Python Script Conventions

All Python helper scripts follow patterns defined in `.claude/misc/PYTHON_HELPER_SCRIPTS.md`:

#### Running Scripts
```bash
# NEVER use arbitrary python commands
# ALWAYS create scripts and run with uv
uv run scripts/script_name.py

# All scripts should support --help
uv run scripts/script_name.py --help
```

#### Script Dependencies (PEP-723)
Scripts use inline metadata for dependencies:
```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "boto3",
#   "python-dotenv>=1.0.0",
# ]
# ///
```

#### Naming Convention
Format: `<verb>_<name_of_task>.py`

Key verbs:
- `explore`, `discover`, `analyse` - research/investigation tasks
- `triage` - collate logs/tests and suggest next steps
- `process`, `export`, `extract`, `migrate`, `convert` - idempotent transformations
- `fix` - temporary one-off fixes

#### Standard Script Structure

Every script should include:

1. **Configuration at top** (all caps variables)
   ```python
   SCRIPT = Path(__file__)
   SCRIPT_NAME = SCRIPT.stem
   SCRIPT_DIR = SCRIPT.parent.resolve()
   PROJECT_ROOT = SCRIPT_DIR.parent
   CACHE_DIR = PROJECT_ROOT / "tmp" / "claude_cache" / SCRIPT_NAME
   ```

2. **Cache checking** (default 5 minutes/300 seconds)
   ```python
   def check_cache(cache_dir: Path, all_input_files: list[Path],
                   timeout: int = 300, force: bool = False) -> tuple[int, int]:
       """Returns (delta, remaining) where both positive = valid cache"""
   ```

3. **Logging (not print statements)**
   ```python
   import logging
   log = logging.getLogger(__name__)
   ```

4. **Standard CLI arguments**
   - `-v/--verbose` - Debug logging
   - `-q/--quiet` - Error-only logging
   - `-f/--force` - Ignore cache (when cache used)
   - `-n/--dry-run` - No changes (when cache used)
   - `--cache-check` - Check cache only (when cache used)

5. **ArgumentParser with comprehensive description**
   ```python
   parser = argparse.ArgumentParser(
       formatter_class=argparse.RawDescriptionHelpFormatter,
       description=dedent(f"""\
       {SCRIPT_NAME} - Description

       INPUTS:
       {_format_file_list(ALL_INPUTS)}

       OUTPUTS:
       {_format_file_list(ALL_OUTPUTS)}

       CACHE: tmp/claude_cache/{SCRIPT_NAME}/
       """)
   )
   ```

#### File Handling
- Use `pathlib.Path` exclusively
- Paths relative to `SCRIPT_DIR` or `PROJECT_ROOT`
- Cache to `tmp/claude_cache/{script_name}/`

#### Helper Functions
Use minimal lambdas at top with `# noqa: E731`:
```python
_run = lambda cmd: subprocess.check_output(split(cmd), text=True).strip()  # noqa: E731
_is_cache_valid = lambda time_tuple: all(x > 0 for x in time_tuple)  # noqa: E731
```

### Failure Modes

**CRITICAL**: Do NOT implement graceful fallbacks unless explicitly directed. The system should either:
- Work correctly as designed, OR
- Fail loudly and halt

Silent failures are worse than no failures. Catch broken parts early.

## Project Structure

```
mcp-fair-shake/
├── src/mcp_fair_shake/    # Main MCP server package
│   ├── __init__.py         # Package exports
│   └── server.py           # FastMCP server with tools (53 lines)
├── tests/                  # Test suite (12 tests, 83.33% coverage)
│   ├── conftest.py         # FastMCP client fixture
│   ├── test_server.py      # Server initialization tests
│   └── test_tools.py       # Tool functionality tests
├── scripts/                # Helper scripts (none yet)
├── .claude/                # Claude Code configuration
│   ├── agents/             # Custom agent definitions
│   ├── commands/           # Custom slash commands (/j:prime, /j:arch, etc.)
│   ├── misc/               # Important documentation
│   │   ├── PRINCIPLES.md   # Development philosophy
│   │   └── PYTHON_HELPER_SCRIPTS.md  # Script conventions
│   ├── skills/             # Custom skills (adk-testing, vite-react, etc.)
│   └── settings.local.json # Claude Code settings
├── pyproject.toml          # Project metadata and dependencies
├── Makefile                # Common development tasks
├── README.md               # Project documentation
├── TESTING.md              # Comprehensive testing guide
└── .python-version         # Python 3.12
```

## SerenaMCP Integration

The project integrates with SerenaMCP for project indexing and context management:

```bash
# Create SerenaMCP project configuration (done by make init)
uvx --from git+https://github.com/oraios/serena serena project create \
    --language python --language typescript $(pwd)

# Re-index the project after significant changes
uvx --from git+https://github.com/oraios/serena serena project index
```

The `make check` target automatically re-indexes after successful quality checks.

## Key Files to Reference

When working on this project, always reference:

**MCP Server Development:**
- `src/mcp_fair_shake/server.py` - FastMCP server implementation patterns
- `tests/test_tools.py` - FastMCP testing patterns
- `TESTING.md` - Comprehensive testing guide with examples
- `README.md` - Project documentation and architecture

**Python Scripting:**
- `.claude/misc/PRINCIPLES.md` - Core development philosophy and pragmatic filtering criteria
- `.claude/misc/PYTHON_HELPER_SCRIPTS.md` - Complete Python scripting conventions

**Development:**
- `Makefile` - Available development commands and targets
- `pyproject.toml` - Dependencies, coverage requirements, tool configurations

## Common Patterns

### Git Integration in Scripts
```python
import subprocess
from shlex import split

_run = lambda cmd: subprocess.check_output(split(cmd), text=True).strip()  # noqa: E731

GIT_ROOT = Path(_run("git rev-parse --show-toplevel"))
GIT_BRANCH = _run("git rev-parse --abbrev-ref HEAD")
```

### Triage Script Output
Triage scripts should output structured sections:
- **STATUS SUMMARY** - Current state with metrics
- **FINDINGS** - Categorized issues (Critical/High/Medium/Low)
- **RECOMMENDATIONS** - Prioritized next steps with confidence levels
- **EVIDENCE LINKS** - Specific files/lines supporting conclusions
- **ASSUMPTIONS** - What analysis assumes true
- **ALTERNATIVES** - Other hypotheses considered and rejected

## FastMCP Development Patterns

### Adding New Tools

Follow this pattern when adding tools to `src/mcp_fair_shake/server.py`:

```python
@mcp.tool()
def new_tool(param1: str, param2: int) -> str:
    """Tool description that will be shown to the LLM.

    Args:
        param1: Description of parameter (type hints are required)
        param2: Description of parameter

    Returns:
        Description of return value

    Example:
        >>> new_tool("value", 42)
        "Expected output format"
    """
    # Validate parameters if needed
    if not param1:
        return "Error: param1 is required"

    # Implement tool logic
    result = f"Processed {param1} with {param2}"

    return result
```

### Testing New Tools

Add tests in `tests/test_tools.py` following FastMCP patterns:

```python
@pytest.mark.asyncio
async def test_new_tool_basic(client: Client[Any]) -> None:
    """Test the new tool with basic inputs."""
    result = await client.call_tool(
        "new_tool",
        arguments={"param1": "test", "param2": 42},
    )

    assert result is not None
    assert result.data is not None
    assert "test" in result.data
```

Use parametrized tests for comprehensive coverage:

```python
@pytest.mark.parametrize(
    ("param1", "param2"),
    [
        ("value1", 10),
        ("value2", 20),
        ("value3", 30),
    ],
)
async def test_new_tool_parametrized(
    client: Client[Any], param1: str, param2: int
) -> None:
    """Test with various inputs."""
    result = await client.call_tool(
        "new_tool",
        arguments={"param1": param1, "param2": param2},
    )
    assert param1 in result.data
```

### FastMCP Benefits

- ✅ **Clean Code**: Simple decorators, no boilerplate
- ✅ **Fast Tests**: In-memory testing (0.12s vs 5s subprocess)
- ✅ **Type Safe**: Full mypy support with strict mode
- ✅ **Clear Errors**: Proper exceptions that "fail loudly"
- ✅ **Great DX**: Intuitive API, excellent documentation

## Quality Standards

The project follows these quality tools:
- **FastMCP** for MCP server development with clean testing
- **Ruff** for formatting and linting (replaces Black, isort, flake8, etc.)
- **mypy** for strict static type checking
- **pytest** with 80% minimum coverage requirement
- **md-toc** for markdown table of contents generation

**All quality checks must ALWAYS pass:**
- `make test` must pass before commits
- `make check` must pass before merges
- Coverage must be ≥ 80%

The `make check` target automatically re-indexes with SerenaMCP after successful quality checks.
