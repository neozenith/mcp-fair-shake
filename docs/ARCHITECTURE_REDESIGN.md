# Architecture Redesign: Knowledge Graph System

## Current Problems

### 1. Output is Unstructured "Slop"
- Navigation elements mixed with content
- Table of contents collapsed into unreadable strings
- No hierarchy preservation
- Cannot query by specific section/subsection
- No cross-references or relationships

### 2. No Type Safety
- Functions return `str` or `dict[str, str]`
- No validation of structure
- No IDE autocomplete support
- Easy to break contracts

### 3. Monolithic Scraper
- All scraping logic in `fetcher.py`
- HTML vs PDF parsing tightly coupled
- Cannot extend for different legislation sources
- Violates Open/Closed Principle

## New Architecture: State-of-the-Art Knowledge Graph

### Core Principles

1. **Structured Parsing** - Parse legislation into proper hierarchical structure
2. **Type Safety** - Pydantic models throughout
3. **Plugin Architecture** - Dependency injection for scrapers
4. **Knowledge Graph** - DuckDB for graph storage and querying
5. **Visualization** - Web UI for exploring relationships

---

## Phase 2.5: Knowledge Graph Redesign

### 1. Pydantic Models for Legislation Structure

```python
from pydantic import BaseModel, Field
from datetime import date
from enum import Enum

class CitationType(str, Enum):
    """Types of legal citations."""
    ACT = "act"
    SECTION = "section"
    SUBSECTION = "subsection"
    PARAGRAPH = "paragraph"
    REGULATION = "regulation"
    ARTICLE = "article"

class LegislationNode(BaseModel):
    """Base node for all legislation elements."""
    id: str  # Canonical ID
    type: CitationType
    number: str | None = None  # Section number, e.g., "394"
    title: str
    content: str  # The actual legal text
    parent_id: str | None = None
    children_ids: list[str] = Field(default_factory=list)

    # Metadata
    enacted_date: date | None = None
    effective_date: date | None = None
    amended_dates: list[date] = Field(default_factory=list)
    repealed_date: date | None = None

    # Cross-references
    references: list[str] = Field(default_factory=list)  # IDs this node cites
    referenced_by: list[str] = Field(default_factory=list)  # IDs that cite this node

class Act(LegislationNode):
    """Top-level Act."""
    type: CitationType = CitationType.ACT
    jurisdiction: str  # "au-federal", "au-victoria"
    year: int
    parts: list[str] = Field(default_factory=list)  # Part IDs

class Part(LegislationNode):
    """Part of an Act."""
    type: CitationType = CitationType.ACT
    act_id: str
    part_number: str  # "1-1", "2-3"
    divisions: list[str] = Field(default_factory=list)

class Division(LegislationNode):
    """Division within a Part."""
    part_id: str
    division_number: str
    sections: list[str] = Field(default_factory=list)

class Section(LegislationNode):
    """Section of legislation (most important for citations)."""
    type: CitationType = CitationType.SECTION
    division_id: str | None = None
    part_id: str | None = None
    act_id: str
    section_number: str  # "394", "21"
    subsections: list[str] = Field(default_factory=list)

    # For unfair dismissal example: /au-federal/fwa/2009/s394
    @property
    def canonical_id(self) -> str:
        return f"{self.act_id}/s{self.section_number}"

class Subsection(LegislationNode):
    """Subsection within a Section."""
    type: CitationType = CitationType.SUBSECTION
    section_id: str
    subsection_number: str  # "1", "2a"
    paragraphs: list[str] = Field(default_factory=list)

class Paragraph(LegislationNode):
    """Paragraph within a Subsection."""
    type: CitationType = CitationType.PARAGRAPH
    subsection_id: str
    paragraph_letter: str  # "a", "b", "c"
```

### 2. Plugin-Based Scraper Architecture

```python
from abc import ABC, abstractmethod
from typing import Protocol

class LegislationParser(Protocol):
    """Protocol for legislation parsers (Dependency Injection)."""

    def can_parse(self, url: str, content_type: str) -> bool:
        """Check if this parser can handle the given URL/content type."""
        ...

    def parse(self, content: bytes, metadata: dict) -> Act:
        """Parse content into structured Act with all nodes."""
        ...

class FederalHTMLParser:
    """Parser for legislation.gov.au HTML."""

    def can_parse(self, url: str, content_type: str) -> bool:
        return "legislation.gov.au" in url and "text/html" in content_type

    def parse(self, content: bytes, metadata: dict) -> Act:
        """Parse HTML into structured Act."""
        soup = BeautifulSoup(content, "lxml")

        # Extract structure from HTML
        act = Act(
            id=metadata["canonical_id"],
            title=self._extract_title(soup),
            content="",
            jurisdiction=metadata["jurisdiction"],
            year=metadata["year"],
        )

        # Parse Parts
        for part_elem in soup.select(".Part"):
            part = self._parse_part(part_elem, act.id)
            act.parts.append(part.id)

        return act

class VictorianPDFParser:
    """Parser for Victorian legislation PDFs."""

    def can_parse(self, url: str, content_type: str) -> bool:
        return "legislation.vic.gov.au" in url and "pdf" in content_type

    def parse(self, content: bytes, metadata: dict) -> Act:
        """Parse PDF into structured Act."""
        reader = PdfReader(BytesIO(content))

        # PDF parsing logic...
        # Extract structure from page markers, headings, etc.
        ...

class ParserRegistry:
    """Registry of available parsers."""

    def __init__(self):
        self.parsers: list[LegislationParser] = []

    def register(self, parser: LegislationParser):
        self.parsers.append(parser)

    def get_parser(self, url: str, content_type: str) -> LegislationParser:
        for parser in self.parsers:
            if parser.can_parse(url, content_type):
                return parser
        raise ValueError(f"No parser found for {url} ({content_type})")

# Usage with Dependency Injection
registry = ParserRegistry()
registry.register(FederalHTMLParser())
registry.register(VictorianPDFParser())
registry.register(ModernAwardPDFParser())

fetcher = LegislationFetcher(parser_registry=registry)
```

### 3. DuckDB Knowledge Graph Storage

```python
import duckdb
from pathlib import Path

class LegislationGraph:
    """DuckDB-based knowledge graph for legislation."""

    def __init__(self, db_path: Path):
        self.conn = duckdb.connect(str(db_path))
        self._create_schema()

    def _create_schema(self):
        """Create graph schema."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id VARCHAR PRIMARY KEY,
                type VARCHAR NOT NULL,
                number VARCHAR,
                title VARCHAR NOT NULL,
                content TEXT NOT NULL,
                parent_id VARCHAR,

                -- Metadata
                enacted_date DATE,
                effective_date DATE,
                repealed_date DATE,

                -- For filtering
                jurisdiction VARCHAR,
                act_id VARCHAR,
                year INTEGER,

                -- Full text search
                content_fts TEXT,

                FOREIGN KEY (parent_id) REFERENCES nodes(id)
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                from_id VARCHAR NOT NULL,
                to_id VARCHAR NOT NULL,
                edge_type VARCHAR NOT NULL,  -- 'cites', 'amends', 'repeals', 'parent_of'
                PRIMARY KEY (from_id, to_id, edge_type),
                FOREIGN KEY (from_id) REFERENCES nodes(id),
                FOREIGN KEY (to_id) REFERENCES nodes(id)
            )
        """)

        # Create full-text search index
        self.conn.execute("""
            INSTALL fts;
            LOAD fts;
            PRAGMA create_fts_index('nodes', 'id', 'content_fts');
        """)

    def insert_act(self, act: Act):
        """Insert Act and all children into graph."""
        self._insert_node(act)

        for part_id in act.parts:
            part = self._get_cached_part(part_id)
            self._insert_node(part)
            self._insert_edge(act.id, part.id, "parent_of")

            for division_id in part.divisions:
                division = self._get_cached_division(division_id)
                self._insert_node(division)
                self._insert_edge(part.id, division.id, "parent_of")

                for section_id in division.sections:
                    section = self._get_cached_section(section_id)
                    self._insert_node(section)
                    self._insert_edge(division.id, section.id, "parent_of")

                    # Insert cross-references
                    for ref_id in section.references:
                        self._insert_edge(section.id, ref_id, "cites")

    def get_section(self, canonical_id: str) -> Section | None:
        """Retrieve specific section by canonical ID."""
        result = self.conn.execute("""
            SELECT * FROM nodes WHERE id = ? AND type = 'section'
        """, [canonical_id]).fetchone()

        if result:
            return Section(**dict(result))
        return None

    def search_full_text(self, query: str, jurisdiction: str | None = None) -> list[Section]:
        """Full-text search across all legislation."""
        sql = """
            SELECT * FROM nodes
            WHERE fts_main_nodes.match_bm25(id, ?)
        """
        params = [query]

        if jurisdiction:
            sql += " AND jurisdiction = ?"
            params.append(jurisdiction)

        sql += " ORDER BY fts_main_nodes.score LIMIT 50"

        results = self.conn.execute(sql, params).fetchall()
        return [Section(**dict(r)) for r in results]

    def get_related_sections(self, section_id: str, depth: int = 2) -> list[Section]:
        """Get sections related by citation graph (BFS)."""
        sql = """
            WITH RECURSIVE related AS (
                SELECT to_id as id, 1 as depth
                FROM edges
                WHERE from_id = ? AND edge_type = 'cites'

                UNION

                SELECT e.to_id, r.depth + 1
                FROM related r
                JOIN edges e ON r.id = e.from_id
                WHERE r.depth < ? AND e.edge_type = 'cites'
            )
            SELECT DISTINCT n.*
            FROM related r
            JOIN nodes n ON r.id = n.id
            WHERE n.type = 'section'
        """

        results = self.conn.execute(sql, [section_id, depth]).fetchall()
        return [Section(**dict(r)) for r in results]

    def export_graph_json(self) -> dict:
        """Export graph for visualization."""
        nodes = self.conn.execute("SELECT * FROM nodes").fetchall()
        edges = self.conn.execute("SELECT * FROM edges").fetchall()

        return {
            "nodes": [dict(n) for n in nodes],
            "edges": [dict(e) for e in edges],
        }
```

### 4. Web UI for Knowledge Graph Visualization

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Fair Shake Knowledge Graph")
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")

graph = LegislationGraph(Path("data/legislation.db"))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main graph visualization page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/graph")
async def get_graph(jurisdiction: str | None = None):
    """Get graph data for visualization."""
    return graph.export_graph_json()

@app.get("/api/section/{section_id}")
async def get_section(section_id: str):
    """Get specific section details."""
    section = graph.get_section(section_id)
    if section:
        return section.model_dump()
    return {"error": "Section not found"}

@app.get("/api/search")
async def search(q: str, jurisdiction: str | None = None):
    """Full-text search."""
    results = graph.search_full_text(q, jurisdiction)
    return [r.model_dump() for r in results]

@app.get("/api/related/{section_id}")
async def get_related(section_id: str, depth: int = 2):
    """Get related sections (citation graph)."""
    related = graph.get_related_sections(section_id, depth)
    return [r.model_dump() for r in related]
```

**Frontend (web/templates/index.html):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Fair Shake Knowledge Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://unpkg.com/force-graph"></script>
</head>
<body>
    <div id="search">
        <input type="text" id="query" placeholder="Search legislation..." />
        <button onclick="search()">Search</button>
    </div>

    <div id="graph"></div>

    <script>
        // Force-directed graph visualization
        const graph = ForceGraph()
            (document.getElementById('graph'))
            .graphData({ nodes: [], links: [] })
            .nodeLabel('title')
            .nodeColor(node => {
                if (node.type === 'section') return '#ff6b6b';
                if (node.type === 'part') return '#4ecdc4';
                return '#95a5a6';
            })
            .onNodeClick(node => {
                fetch(`/api/section/${node.id}`)
                    .then(r => r.json())
                    .then(data => showDetails(data));
            });

        // Load graph data
        fetch('/api/graph')
            .then(r => r.json())
            .then(data => {
                graph.graphData({
                    nodes: data.nodes,
                    links: data.edges.map(e => ({
                        source: e.from_id,
                        target: e.to_id,
                        type: e.edge_type
                    }))
                });
            });

        function search() {
            const query = document.getElementById('query').value;
            fetch(`/api/search?q=${encodeURIComponent(query)}`)
                .then(r => r.json())
                .then(results => displayResults(results));
        }
    </script>
</body>
</html>
```

### 5. Updated MCP Tools with Structured Output

```python
from mcp_fair_shake.models import Section

@mcp.tool()
def get_legislation_section(
    canonical_id: str,
    include_related: bool = False,
) -> dict:
    """Get specific legislation section with full structure.

    Args:
        canonical_id: Section ID (e.g., "/au-federal/fwa/2009/s394")
        include_related: Include related sections from citation graph

    Returns:
        Structured section data with hierarchy and cross-references
    """
    section = graph.get_section(canonical_id)

    if not section:
        return {"error": f"Section {canonical_id} not found"}

    result = section.model_dump()

    if include_related:
        related = graph.get_related_sections(canonical_id, depth=2)
        result["related_sections"] = [r.model_dump() for r in related]

    return result
```

---

## Implementation Plan

### Phase 2.5 - Week 1: Pydantic Models & Parser Architecture

**Day 1-2:**
- [ ] Define Pydantic models (`models/legislation.py`)
- [ ] Create parser protocol and registry
- [ ] Write tests for model validation

**Day 3-4:**
- [ ] Implement Federal HTML parser (extract structure)
- [ ] Implement Victorian PDF parser
- [ ] Test parsers with real legislation

**Day 5:**
- [ ] Integrate parsers with fetcher
- [ ] Update tests
- [ ] Verify structured output

### Phase 2.5 - Week 2: DuckDB Knowledge Graph

**Day 6-7:**
- [ ] Design DuckDB schema
- [ ] Implement LegislationGraph class
- [ ] Write graph insertion logic
- [ ] Full-text search with FTS extension

**Day 8-9:**
- [ ] Cross-reference extraction
- [ ] Citation graph queries
- [ ] Export functionality

**Day 10:**
- [ ] Migrate existing cached legislation to graph
- [ ] Verify data integrity
- [ ] Performance testing

### Phase 2.5 - Week 3: Web UI

**Day 11-12:**
- [ ] FastAPI server setup
- [ ] API endpoints for graph data
- [ ] Basic HTML templates

**Day 13-14:**
- [ ] D3.js / Force-Graph visualization
- [ ] Interactive node exploration
- [ ] Search interface

**Day 15:**
- [ ] Polish UI
- [ ] Documentation
- [ ] CLI command: `mcp-fair-shake serve`

---

## Success Criteria

**Structured Parsing:**
- ✅ Can retrieve Section 394 of Fair Work Act with full hierarchy
- ✅ Subsections, paragraphs properly nested
- ✅ Cross-references extracted and linked

**Type Safety:**
- ✅ All functions use Pydantic models
- ✅ IDE autocomplete works
- ✅ Validation catches structural errors

**Plugin Architecture:**
- ✅ Can add new parser without modifying fetcher
- ✅ Parser registry uses dependency injection
- ✅ Each jurisdiction has dedicated parser

**Knowledge Graph:**
- ✅ DuckDB stores full graph structure
- ✅ Can query "all sections that cite s394"
- ✅ Full-text search across all legislation
- ✅ Graph export for visualization

**Web UI:**
- ✅ Force-directed graph visualization
- ✅ Click node to see details
- ✅ Search and filter
- ✅ Citation graph exploration

---

## File Structure

```
mcp-fair-shake/
├── src/mcp_fair_shake/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── legislation.py          # Pydantic models
│   │   └── metadata.py
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py                 # Parser protocol
│   │   ├── registry.py             # Parser registry
│   │   ├── federal_html.py         # Federal HTML parser
│   │   ├── victorian_pdf.py        # Victorian PDF parser
│   │   └── modern_award_pdf.py     # Modern Award parser
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── duckdb_graph.py         # DuckDB graph storage
│   │   └── queries.py              # Graph query helpers
│   ├── web/
│   │   ├── __init__.py
│   │   ├── server.py               # FastAPI server
│   │   ├── templates/
│   │   │   └── index.html
│   │   └── static/
│   │       ├── css/
│   │       └── js/
│   ├── fetcher.py                  # Simplified with DI
│   ├── server.py                   # MCP server
│   └── cli.py                      # CLI with 'serve' command
├── data/
│   ├── legislation.db              # DuckDB database
│   └── legislation/
│       └── cache/                  # Raw files (legacy)
└── tests/
    ├── test_models.py
    ├── test_parsers.py
    ├── test_graph.py
    └── test_web.py
```

---

## Migration Strategy

1. **Keep existing cache** - Don't delete current text files
2. **Build graph in parallel** - New DuckDB database alongside cache
3. **Migrate incrementally** - Parse and import one Act at a time
4. **Verify with tests** - Compare structured output with original text
5. **Switch tools** - Update MCP tools to use graph once verified
6. **Deprecate cache** - Remove text files after successful migration
