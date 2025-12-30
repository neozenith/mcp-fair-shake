# Ensure the .make folder exists when starting make
# We need this for build targets that have multiple or no file output.
# We 'touch' files in here to mark the last time the specific job completed.
_ := $(shell mkdir -p .make)
SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

.PHONY: docs init fix check docs test claude frontend-install frontend-dev frontend-agentic-dev frontend-build frontend-check frontend-test

#########################################################################################
# Project Setup
#########################################################################################

.serena/project.yml:
	uvx --from git+https://github.com/oraios/serena serena project create --language python --language typescript $$(pwd)

init: .make/init .serena/project.yml
.make/init:
	uv sync --dev

	# Initialize SerenaMCP project if not already done
	# uvx --from git+https://github.com/oraios/serena serena project create --language python --language typescript $$(pwd)

	uvx --from git+https://github.com/oraios/serena serena project index
	@touch $@

fix: init
	uv run ruff format .
	uv run ruff check . --fix

check: init docs fix
	uv sync --dev
	uv run ruff check . --diff
	uv run ruff format . --check --diff
	uv run mypy src/

	# As long as the whole project is formatted, linted, type checked, and tested then we can update the symbol index for SerenaMCP
	uvx --from git+https://github.com/oraios/serena serena project index

docs: init
	uvx --from md-toc md_toc --in-place github --header-levels 4 *.md

test: init check
	uv run pytest -v

#########################################################################################
# Development
#########################################################################################

claude: test
	@echo "✅ All checks passed! Launching Claude Code with MCP Fair Shake configured..."
	@echo ""
	@echo "MCP Server: mcp-fair-shake"
	@echo "Config: $$(pwd)/mcp-config.json"
	@echo "Project: $$(pwd)"
	@echo ""
	claude --mcp-config $$(pwd)/mcp-config.json

#########################################################################################
# Frontend Development
#########################################################################################

frontend-install:
	npm --prefix frontend install

frontend-dev: frontend-install
	@echo "🚀 Starting development servers..."
	@echo "   Backend:  http://localhost:8100"
	@echo "   Frontend: http://localhost:5273"
	@echo ""
	npm --prefix frontend run dev

frontend-agentic-dev: frontend-install
	@echo "🤖 Starting agentic development servers..."
	@echo "   Backend:  http://localhost:8101"
	@echo "   Frontend: http://localhost:5274"
	@echo ""
	npm --prefix frontend run agentic-dev

frontend-build: frontend-install
	npm --prefix frontend run build

frontend-check: frontend-install
	@echo "🔍 Running frontend quality checks..."
	npm --prefix frontend run lint
	@echo "✅ TypeScript compilation check..."
	npm --prefix frontend run type-check
	@echo "✅ Frontend checks passed!"

frontend-test: frontend-install frontend-check
	@echo "🧪 Running frontend tests..."
	@echo "⚠️  Frontend tests not yet implemented"
	@echo "    Will add: Vitest + React Testing Library"
	@echo "✅ Frontend test target ready for implementation"

clean:
	rm -rf .make
	rm -rf .*_cache
	rm -rf __pycache__/
	rm -rf scripts/
	rm -rf frontend/node_modules
	rm -rf frontend/dist
