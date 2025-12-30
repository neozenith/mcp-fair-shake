# Next Steps: Knowledge Graph Redesign

## Executive Summary

**Current State**: We have 17 Acts cached, but the output is unstructured "slop" - just raw text with navigation elements mixed in. You cannot retrieve specific sections, there's no hierarchy, and no relationships.

**Target State**: A state-of-the-art knowledge graph where you can query "Section 394 of the Fair Work Act" and get back structured data with full hierarchy, cross-references, and citation graph.

**Priority**: Phase 2.5 is now P0 (highest priority) - blocks all other phases.

---

## What Changed

### Old Priority Order
1. ~~Phase 5: National Coverage (all states/territories)~~ ❌ **DEFERRED**
2. Phase 2: Victorian Coverage enhancements
3. Phase 6: Advanced Features (DuckDB, embeddings)

### New Priority Order
1. **Phase 2.5: Knowledge Graph Redesign** 🔴 **CURRENT PRIORITY**
2. Phase 6: Advanced Features (integrated with Phase 2.5)
3. Phase 5: National Coverage (lowest priority - deferred)

**Rationale**: "Quality over quantity - perfect the small scope first"

---

## Phase 2.5: 3-Week Plan

### Week 1: Pydantic Models & Parser Plugins

**Goal**: Replace string returns with typed Pydantic models and implement dependency injection for parsers.

**Deliverables**:
```python
# Before (slop):
def fetch(canonical_id: str) -> str:
    return "# Fair Work Act 2009\n\nCollapseVolume 1CollapseChapter..."

# After (structured):
def fetch(canonical_id: str) -> Act:
    return Act(
        id="/au-federal/fwa/2009",
        title="Fair Work Act 2009",
        jurisdiction="au-federal",
        year=2009,
        parts=[
            Part(
                id="/au-federal/fwa/2009/part-1-1",
                part_number="1-1",
                title="Introduction",
                divisions=[
                    Division(
                        id="/au-federal/fwa/2009/part-1-1/div-1",
                        division_number="1",
                        title="Preliminary",
                        sections=[
                            Section(
                                id="/au-federal/fwa/2009/s394",
                                section_number="394",
                                title="Meaning of unfair dismissal",
                                content="A person has been unfairly dismissed if...",
                                subsections=[...],
                                references=["/au-federal/fwa/2009/s385"],
                            )
                        ]
                    )
                ]
            )
        ]
    )
```

**Tasks**:
- [ ] Define Pydantic models (`src/mcp_fair_shake/models/legislation.py`)
- [ ] Create parser protocol (`src/mcp_fair_shake/parsers/base.py`)
- [ ] Implement parser registry with DI (`src/mcp_fair_shake/parsers/registry.py`)
- [ ] Build Federal HTML parser (`src/mcp_fair_shake/parsers/federal_html.py`)
- [ ] Build Victorian PDF parser (`src/mcp_fair_shake/parsers/victorian_pdf.py`)
- [ ] Write tests (80%+ coverage)

**Success**: Can parse Fair Work Act into full Act object with all Parts, Divisions, Sections, Subsections.

### Week 2: DuckDB Knowledge Graph

**Goal**: Store legislation as a queryable graph with nodes (sections) and edges (citations).

**Deliverables**:
```python
graph = LegislationGraph("data/legislation.db")

# Insert Act with full structure
graph.insert_act(fair_work_act)

# Query by canonical ID
section = graph.get_section("/au-federal/fwa/2009/s394")
# Returns: Section(section_number="394", title="Meaning of unfair dismissal", ...)

# Full-text search
results = graph.search_full_text("unfair dismissal", jurisdiction="au-federal")
# Returns: [Section(...), Section(...), ...]

# Citation graph
related = graph.get_related_sections("/au-federal/fwa/2009/s394", depth=2)
# Returns sections that cite or are cited by s394

# Export for visualization
graph_json = graph.export_graph_json()
# Returns: {"nodes": [...], "edges": [...]}
```

**Schema**:
```sql
CREATE TABLE nodes (
    id VARCHAR PRIMARY KEY,
    type VARCHAR NOT NULL,  -- 'act', 'part', 'division', 'section', 'subsection'
    number VARCHAR,
    title VARCHAR NOT NULL,
    content TEXT NOT NULL,
    parent_id VARCHAR,
    jurisdiction VARCHAR,
    act_id VARCHAR,
    year INTEGER,
    FOREIGN KEY (parent_id) REFERENCES nodes(id)
);

CREATE TABLE edges (
    from_id VARCHAR NOT NULL,
    to_id VARCHAR NOT NULL,
    edge_type VARCHAR NOT NULL,  -- 'cites', 'amends', 'repeals', 'parent_of'
    PRIMARY KEY (from_id, to_id, edge_type)
);
```

**Tasks**:
- [ ] Design DuckDB schema
- [ ] Implement `LegislationGraph` class
- [ ] Write insertion logic (Act → nodes + edges)
- [ ] Implement queries (get_section, search_full_text, get_related)
- [ ] Migrate 17 existing Acts to graph
- [ ] Performance testing (< 100ms queries)

**Success**: All 17 Acts in DuckDB graph, can query by section, full-text search works, citation graph traversal works.

### Week 3: Web UI Visualization

**Goal**: Interactive web interface to explore the knowledge graph.

**Deliverables**:
- Force-directed graph visualization (D3.js / force-graph)
- Click nodes to see details
- Search and filter
- Citation graph exploration

**CLI Command**:
```bash
mcp-fair-shake serve
# Opens browser to http://localhost:8000
# Shows interactive graph visualization
```

**API Endpoints**:
```
GET /                          # Main visualization page
GET /api/graph                 # Full graph JSON
GET /api/section/{id}          # Section details
GET /api/search?q=unfair       # Full-text search
GET /api/related/{id}?depth=2  # Citation graph
```

**UI Features**:
- Force-directed graph with color-coded nodes (Act = blue, Part = green, Section = red)
- Click node → Show sidebar with section content
- Search bar → Highlight matching nodes
- Filter by jurisdiction, type
- Show citation paths between sections

**Tasks**:
- [ ] FastAPI server setup
- [ ] API endpoints implementation
- [ ] D3.js / force-graph integration
- [ ] HTML/CSS/JS for interactive UI
- [ ] CLI `serve` command

**Success**: `mcp-fair-shake serve` launches beautiful interactive graph explorer.

---

## Technical Benefits

### 1. Type Safety with Pydantic

**Before**:
```python
def get_legislation_content(canonical_id: str, mode: str = "text") -> str:
    # Returns raw text, no validation
    return "..."
```

**After**:
```python
from pydantic import BaseModel

class Section(BaseModel):
    id: str
    section_number: str
    title: str
    content: str
    subsections: list[Subsection]
    references: list[str]  # IDs this section cites

def get_legislation_section(canonical_id: str) -> Section:
    # IDE autocomplete, validation, type checking
    return Section(...)
```

### 2. Dependency Injection for Parsers

**Before** (monolithic):
```python
def fetch(canonical_id: str) -> str:
    if "legislation.gov.au" in url:
        # HTML parsing logic here
        ...
    elif "legislation.vic.gov.au" in url:
        # PDF parsing logic here
        ...
    # Adding new source = modify this function
```

**After** (plugin-based):
```python
class FederalHTMLParser:
    def can_parse(self, url: str) -> bool:
        return "legislation.gov.au" in url

    def parse(self, content: bytes) -> Act:
        # HTML parsing logic

class VictorianPDFParser:
    def can_parse(self, url: str) -> bool:
        return "legislation.vic.gov.au" in url

    def parse(self, content: bytes) -> Act:
        # PDF parsing logic

# Adding new source = add new parser class (Open/Closed Principle)
registry = ParserRegistry()
registry.register(FederalHTMLParser())
registry.register(VictorianPDFParser())
registry.register(NSWHTMLParser())  # No modification to existing code!
```

### 3. Graph Querying with DuckDB

**Before**:
```python
# Want sections that cite s394?
# Impossible - no relationship data
```

**After**:
```python
# Graph traversal with SQL
related = graph.get_related_sections("/au-federal/fwa/2009/s394", depth=2)

# Behind the scenes:
"""
WITH RECURSIVE related AS (
    SELECT to_id, 1 as depth
    FROM edges
    WHERE from_id = '/au-federal/fwa/2009/s394' AND edge_type = 'cites'

    UNION

    SELECT e.to_id, r.depth + 1
    FROM related r
    JOIN edges e ON r.id = e.from_id
    WHERE r.depth < 2
)
SELECT * FROM nodes WHERE id IN (SELECT to_id FROM related)
"""
```

---

## Migration Plan

**Non-Breaking Approach**:

1. **Build in parallel** - Don't delete existing cache
2. **New modules** - Create `models/`, `parsers/`, `graph/` without touching old code
3. **Parse incrementally** - Start with Fair Work Act, then Victorian Acts
4. **Verify** - Compare structured output with original text
5. **Update MCP tools** - Switch to graph-based once verified
6. **Deprecate cache** - Remove text files after successful migration

**Timeline**:
- Week 1: Parsers ready, can parse Fair Work Act
- Week 2: DuckDB ready, all Acts migrated
- Week 3: Web UI complete, knowledge graph live

---

## Success Metrics

**Phase 2.5 is DONE when**:

✅ Can query: "Get Section 394 of Fair Work Act"
```python
section = graph.get_section("/au-federal/fwa/2009/s394")
assert section.title == "Meaning of unfair dismissal"
assert len(section.subsections) > 0
```

✅ Can search: "unfair dismissal"
```python
results = graph.search_full_text("unfair dismissal")
assert "/au-federal/fwa/2009/s394" in [r.id for r in results]
```

✅ Can traverse: "What sections cite s394?"
```python
related = graph.get_related_sections("/au-federal/fwa/2009/s394")
assert len(related) > 0
```

✅ Web UI works:
```bash
mcp-fair-shake serve
# Browser opens to interactive graph
# Click s394 node → Shows full section details
```

✅ Type safety:
```python
# mypy passes with 100% strict type coverage
# IDE autocomplete works for all models
```

✅ Tests pass:
```bash
make test
# 111+ tests, 85%+ coverage, all passing
```

---

## Next Immediate Actions

**Ready to start?** Here's the first task:

1. Create Pydantic models structure:
   ```bash
   mkdir -p src/mcp_fair_shake/models
   touch src/mcp_fair_shake/models/__init__.py
   touch src/mcp_fair_shake/models/legislation.py
   ```

2. Define base models in `legislation.py`:
   - `CitationType` enum
   - `LegislationNode` base class
   - `Act`, `Part`, `Division`, `Section`, `Subsection`, `Paragraph` classes

3. Write tests first (TDD):
   ```bash
   touch tests/test_models.py
   ```

4. Implement Federal HTML parser:
   ```bash
   mkdir -p src/mcp_fair_shake/parsers
   touch src/mcp_fair_shake/parsers/__init__.py
   touch src/mcp_fair_shake/parsers/base.py
   touch src/mcp_fair_shake/parsers/federal_html.py
   ```

Would you like me to start with Step 1 (Pydantic models)?
