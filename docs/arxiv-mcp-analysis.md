# arXiv MCP Architecture Analysis

This document analyzes the arXiv MCP design patterns and their application to the legislation lookup MCP.

## Overview

The arXiv MCP server enables AI assistants to search academic papers on arXiv, download them locally, and analyze their content. It demonstrates important patterns for **information retrieval with local caching**.

## Core Architecture Pattern

### Four-Tool Pattern

Unlike Context7's two-tool pattern, arXiv uses **four distinct tools**:

1. **search_papers** - Query arXiv with filters
2. **download_paper** - Fetch and cache paper by ID
3. **list_papers** - Show what's in local cache
4. **read_paper** - Access cached paper content

This separates:
- **Discovery** (search)
- **Acquisition** (download)
- **Inventory** (list)
- **Consumption** (read)

### Tool Specifications

#### 1. search_papers
```
Parameters:
- query: str (search terms)
- max_results: int (result limit, default 10)
- date_from: str (format: "YYYY-MM-DD")
- date_to: str (format: "YYYY-MM-DD")
- categories: List[str] (e.g., ["cs.AI", "cs.LG"])

Returns:
- List of paper metadata (title, authors, abstract, arXiv ID)
```

#### 2. download_paper
```
Parameters:
- arxiv_id: str (e.g., "2401.12345")

Returns:
- Success/failure status
- Local storage path

Side Effects:
- Downloads PDF to ~/.arxiv-mcp-server/papers/
- Stores metadata for listing
```

#### 3. list_papers
```
Parameters: None

Returns:
- List of all cached papers with metadata
- Storage paths
- Download timestamps
```

#### 4. read_paper
```
Parameters:
- arxiv_id: str (or local path)

Returns:
- Paper content (extracted text)
- Metadata (title, authors, abstract)
```

## Key Design Patterns

### 1. Local-First Architecture

**Philosophy**: Download once, query many times

Benefits:
- ✅ Fast access after initial download
- ✅ Offline capability
- ✅ Reduced API load on arXiv
- ✅ Persistent storage across sessions

**Storage Structure**:
```
~/.arxiv-mcp-server/
├── papers/
│   ├── 2401.12345.pdf
│   ├── 2402.67890.pdf
│   └── metadata.json
└── config.json
```

### 2. Structured Filtering

Search supports multiple filter dimensions:
- **Temporal**: Date ranges (from/to)
- **Categorical**: Academic categories (cs.AI, physics.quant-ph)
- **Quantitative**: Result limits (max_results)
- **Textual**: Query terms (natural language or field-specific)

### 3. Standard Identifiers

Uses arXiv's canonical ID format: `YYMM.NNNNN`
- Year/month prefix
- Sequential number
- Version suffix (v1, v2, etc.)

Examples:
- `2401.12345` - January 2024, paper #12345
- `2401.12345v2` - Second version of the same paper

### 4. Metadata Management

Tracks downloaded papers with:
- arXiv ID
- Title, authors, abstract
- Download timestamp
- Local file path
- File size
- Categories/tags

### 5. Workflow Automation

Provides specialized prompt templates:
- **deep-paper-analysis**: Search → Download → Analyze
- Automates common multi-step workflows
- Reduces user cognitive load

## Comparison: arXiv vs Context7

| Aspect | Context7 | arXiv | Best for Legislation |
|--------|----------|-------|---------------------|
| **Tool Count** | 2 tools | 4 tools | 3 tools (hybrid) |
| **Resolution** | Separate tool | Part of search | Separate (like Context7) |
| **Caching** | Server-side | Local client-side | Local (like arXiv) |
| **Versioning** | Built into ID | Version suffix | Built into ID |
| **Modes** | Mode parameter | Separate tools | Mode parameter |
| **Pagination** | Page parameter | Max results | Both approaches |
| **Metadata** | Inline with docs | Separate listing | Separate (like arXiv) |

## Application to Legislation MCP

### Proposed Tool Structure (Hybrid Approach)

**3-Tool Pattern** (combines best of both):

#### 1. resolve-legislation (Context7 pattern)
```python
@mcp.tool()
def resolve_legislation(query: str, jurisdiction: str = "all") -> str:
    """Resolve legislation reference to canonical ID.

    Args:
        query: Natural language or citation (e.g., "unfair dismissal", "FWA s.394")
        jurisdiction: Filter by jurisdiction ("federal", "victoria", "all")

    Returns:
        Ranked list of matching legislation with canonical IDs
    """
```

#### 2. get-legislation-content (Context7 pattern + arXiv caching)
```python
@mcp.tool()
def get_legislation_content(
    canonical_id: str,
    section: str = "",
    mode: Literal["text", "summary", "metadata"] = "summary",
    page: int = 1
) -> str:
    """Fetch legislation content from local cache.

    Args:
        canonical_id: Canonical ID from resolve-legislation
        section: Optional section/article filter
        mode: Content type (text/summary/metadata)
        page: Page number for long statutes

    Returns:
        Legislation content in requested format

    Note: Auto-downloads if not cached
    """
```

#### 3. get-support (New for legislation)
```python
@mcp.tool()
def get_support(
    canonical_id: str,
    situation: str = "",
    jurisdiction: str = ""
) -> str:
    """Get support pathways for legislation.

    Args:
        canonical_id: Legislation ID to get support for
        situation: Describe the situation (optional, for filtering)
        jurisdiction: Jurisdiction for support agencies

    Returns:
        Relevant support agencies, contact info, next steps
    """
```

### Data Architecture (Inspired by arXiv)

```
data/
├── legislation/
│   ├── cache/                               # arXiv-style local cache
│   │   ├── au-federal/
│   │   │   ├── fwa-2009.txt                # Raw legislation text
│   │   │   ├── fwa-2009-metadata.json      # Fetch date, source, checksum
│   │   │   └── fwa-2009-sections.json      # Parsed sections
│   │   └── au-victoria/
│   │       ├── ohs-2004.txt
│   │       └── ohs-2004-metadata.json
│   ├── parquet/                             # Optimized for querying
│   │   ├── legislation.parquet             # Main content
│   │   ├── sections.parquet                # Section index
│   │   └── citations.parquet               # Citation mappings
│   └── summaries/                           # Plain language summaries
│       ├── au-federal-fwa-2009-summary.json
│       └── au-victoria-ohs-2004-summary.json
├── support-pathways/
│   ├── federal-agencies.json
│   ├── victoria-agencies.json
│   └── pathways/
│       ├── unfair-dismissal-pathway.json
│       └── wage-theft-pathway.json
└── metadata/
    ├── cache-index.json                     # What's downloaded
    ├── update-log.json                      # Last update checks
    └── checksums.json                       # Content verification
```

### Key Patterns Adopted from arXiv

1. **Local-First Caching**: Download legislation once, query many times
   - Faster access (no network latency)
   - Offline capability
   - Version control for cached content

2. **Structured Filtering**: Multi-dimensional search
   - Jurisdiction (federal/state)
   - Date ranges (enacted, effective, amended)
   - Categories (WHS, discrimination, leave, etc.)
   - Authority level (primary legislation, regulations, guidance)

3. **Metadata Tracking**: Separate metadata files
   - Source URLs
   - Fetch timestamps
   - Checksums for integrity
   - Amendment history

4. **Inventory Management**: Know what's cached
   - Could add `list-cached-legislation` tool (like arXiv's list_papers)
   - Show cache status, freshness, coverage
   - Enable data export and inspection

### Workflow Pattern

```
User: "use fair-shake: What are my rights if I'm casually employed?"
    ↓
1. resolve-legislation("casual employee rights", jurisdiction="victoria")
    ↓
   Returns: [
     "/au-federal/fwa/2009/s86" (Fair Work Act - Casual Employment),
     "/au-victoria/lsl/2018/s7" (Long Service Leave - Casual Eligibility)
   ]
    ↓
2. get-legislation-content(
     canonical_id="/au-federal/fwa/2009/s86",
     mode="summary"
   )
    ↓
   Auto-downloads if not cached (background)
   Returns plain language summary from cache
    ↓
3. get-support(
     canonical_id="/au-federal/fwa/2009/s86",
     situation="casual employment rights"
   )
    ↓
   Returns:
   - Fair Work Ombudsman contact
   - Relevant union information
   - Complaint pathway steps
```

## Advanced Patterns from arXiv

### 1. Automated Workflows

arXiv provides "deep-paper-analysis" prompt that chains:
- Search → Download → Read → Analyze

**For legislation:**
Could provide specialized prompts:
- "unfair-dismissal-check": Resolve → Get content → Get support → Generate checklist
- "wage-review": Search pay rates → Check modern award → Calculate entitlements

### 2. Background Downloads

arXiv downloads papers asynchronously:
- Search returns immediately with metadata
- Downloads happen in background
- Subsequent reads are instant (cached)

**For legislation:**
- First query might trigger background download
- Show progress indicator if fetching
- Cache for future queries
- Preemptive caching of commonly accessed legislation

### 3. Content Extraction

arXiv extracts text from PDFs for analysis

**For legislation:**
- Parse HTML/XML from government websites
- Extract section structure
- Build citation index
- Generate plain language summaries (Phase 2+)

## Recommendations

### Adopt from arXiv:
1. ✅ **Local-first caching** - Critical for fast, reliable access
2. ✅ **Metadata tracking** - Know what's cached, when fetched, source integrity
3. ✅ **Structured filtering** - Multi-dimensional search (jurisdiction, date, category)
4. ✅ **Inventory tool** - Optional `list-cached-legislation` for transparency

### Adopt from Context7:
1. ✅ **Two-step resolution** - Separate resolve from content retrieval
2. ✅ **Mode parameter** - text/summary/metadata in one tool
3. ✅ **Ranking logic** - Smart selection when multiple matches
4. ✅ **Pagination** - Handle long statutes gracefully

### Unique to Legislation:
1. ✅ **Support pathways** - `get-support` tool for actionable guidance
2. ✅ **Jurisdiction hierarchy** - Federal vs. state vs. local
3. ✅ **Amendment tracking** - Historical versions with effective dates
4. ✅ **Cross-references** - Related regulations, case law, guidance

## Key Differences: Academic Papers vs. Legislation

| Aspect | arXiv Papers | Legislation |
|--------|-------------|-------------|
| **Versioning** | v1, v2 (author revisions) | Amendments (parliamentary process) |
| **Authority** | Peer review varies | Government authority (hierarchical) |
| **Stability** | Papers don't change post-publication | Legislation amended frequently |
| **Structure** | Sections, figures, references | Sections, subsections, schedules |
| **Access** | Free, open access | Free, government websites |
| **Updates** | New papers daily | Amendments on legislative schedule |
| **Identifiers** | arXiv ID (2401.12345) | Multiple citation formats (USC, CFR, etc.) |

## Sources

- [arXiv MCP Server GitHub](https://github.com/blazickjp/arxiv-mcp-server)
- [arXiv MCP on PulseMCP](https://www.pulsemcp.com/servers/blazickjp-arxiv-mcp-server)
- [arXiv MCP on LobeHub](https://lobehub.com/mcp/blazickjp-arxiv-mcp-server)
- [MCP Interoperability Survey (arXiv)](https://arxiv.org/html/2505.02279v1)
- [ResourceLink Patterns (arXiv)](https://arxiv.org/html/2510.05968v1)
