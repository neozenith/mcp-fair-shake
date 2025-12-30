# MCP Fair Shake - Implementation Roadmap

**Version:** 1.1
**Last Updated:** 2025-12-24
**Current Phase:** Phase 1 → **CRITICAL BLOCKER IDENTIFIED**

---

## 🔴 CRITICAL BLOCKER - Victorian Legislation Not Available in HTML

**Issue**: Victorian `legislation.vic.gov.au` **does NOT provide HTML versions** of legislation. The website only provides PDF and DOCX downloads.

**Investigation Summary** (2025-12-24):
1. ✅ **HTML Parser** - Working perfectly (tests pass)
2. ✅ **Playwright** - Working perfectly (fetches JavaScript-rendered pages)
3. ✅ **Federal legislation** - Works perfectly (legislation.gov.au provides HTML)
4. ❌ **Victorian legislation** - legislation.vic.gov.au pages only contain:
   - Navigation menus
   - Download links to PDF files
   - Download links to DOCX files
   - **NO actual legislation HTML content**

**Evidence**:
- Tested URL: `https://www.legislation.vic.gov.au/in-force/acts/occupational-health-and-safety-act-2004/045`
- Page HTML: 97KB of HTML
- Extracted content: 105 bytes (only "Authorised version 04-107aa045 authorised.PDF")
- Playwright successfully renders JavaScript, but there's no legislation content to render
- AustLII (third-party) HTML URLs return 410 Gone

**Impact**:
- Victorian legislation cannot be fetched in HTML format from official sources
- Federal legislation works perfectly (Fair Work Act: 770KB of real content)
- **This blocks Phase 1 completion** (requires Victorian OHS Act)

**Solutions** (Choose one):

**Option 1: PDF Parsing** (Recommended)
- ✅ Use official Victorian government PDFs
- ✅ Authoritative source (legislation.vic.gov.au)
- ❌ Complex parsing (tables, formatting, multi-column layouts)
- ❌ Larger file downloads (1-2MB per Act vs. HTML)
- ❌ Requires PDF library (pypdf, pdfplumber, or PyMuPDF)

**Option 2: Defer Victorian Legislation**
- ✅ Focus on federal legislation (works perfectly)
- ✅ Complete Phase 4 first (federal coverage)
- ❌ Doesn't meet project goals (employee-first, Victorian coverage)
- ❌ User explicitly requested Victorian legislation

**Option 3: Find Alternative HTML Source**
- ✅ Would work with existing HTML parser
- ❌ No authoritative HTML sources found (AustLII outdated)
- ❌ Third-party sources may not be current or complete

**Recommended Action**: Implement PDF parsing (Option 1)
- Library: `pypdf` or `pdfplumber` (both actively maintained)
- Download PDFs from legislation.vic.gov.au
- Extract text while preserving structure
- Cache extracted text (same as HTML fetching)

**Required Actions**:
1. **[COMPLETED 2025-12-24]** Add PDF parsing library: `uv add pypdf`
2. **[COMPLETED 2025-12-24]** Implement `_download_pdf()` and `_parse_pdf_content()` methods
3. **[COMPLETED 2025-12-24]** Update `fetch_async()` to detect PDF-only sources
4. **[COMPLETED 2025-12-24]** Write tests for PDF parsing (TDD) - 7/7 tests pass
5. **[COMPLETED 2025-12-24]** Update Victorian legislation URLs to PDF download links
6. **[IN PROGRESS]** Clear cache and re-fetch Victorian legislation as PDFs
7. **[PENDING]** Update documentation to reflect PDF parsing approach

**Implementation Details**:
- PDF parsing with full audit trail (page numbers, source URL, PDF metadata)
- Extracted content includes `[Page N]` markers for accurate legal citations
- Metadata includes: author, creator, creation_date, modification_date, page_count
- Content hash (SHA-256) for integrity verification
- Test coverage: 7 tests covering extraction, page markers, metadata, structure preservation

**Status**: 🟢 **RESOLVED** - PDF parsing implemented and tested

---

## Quick Reference

| Phase | Focus | Duration | Status |
|-------|-------|----------|--------|
| **Phase 1** | MVP - Victorian OHS Act | Weeks 1-2 | 🟢 Complete |
| **Phase 2** | Victorian Coverage | Weeks 3-4 | ⚪ Not Started |
| **Phase 3** | Support Pathways | Weeks 5-6 | ⚪ Not Started |
| **Phase 4** | Federal Coverage | Weeks 7-9 | ⚪ Not Started |
| **Phase 5** | National Coverage | Weeks 10-15 | ⚪ Not Started |
| **Phase 6** | Advanced Features | Future | ⚪ Not Started |

## Phase 1: MVP - Unfair Dismissal (Federal + Victorian) (Weeks 1-3)

**Goal**: Validate core functionality with unfair dismissal use case

### Core Mission
**Reduce the cost of having timely, grounded, and factual legislation in the hands of employees via AI chat assistants.**

### Objectives
- ✅ Implement four-tool MCP pattern (resolve, get-content, get-cache-status, + CLI)
- ✅ Prove local-first caching works (federal + state legislation)
- ✅ Establish TDD workflow and quality standards
- ✅ Validate unfair dismissal use case end-to-end
- ✅ Pre-cache P0 legislation (4 MB)

### Scope

**Primary Use Case: Unfair Dismissal**
- Employee believes they were unfairly dismissed
- Need to understand rights and FWC claim process
- 21-day deadline is critical
- Query: "use fair-shake: I think I was unfairly dismissed, what are my rights?"

**Legislation (P0 Priority - MVP Complete):**
1. **Fair Work Act 2009 (Federal)** - ~2.5 MB, 789 sections
   - Focus: Part 3-2 (unfair dismissal provisions)
   - Key sections: s.385-398
   - Full Act cached for completeness
2. **Victorian OHS Act 2004** - ~500 KB, 157 sections
   - Workplace safety baseline
3. **Victorian Equal Opportunity Act 2010** - ~350 KB, 128 sections
   - Discrimination protections

**Total MVP Database**: ~4 MB raw text (~2.4 MB Parquet)

### Tools

1. **resolve-legislation**
   - Citation matching for unfair dismissal queries
   - Natural language: "unfair dismissal" → `/au-federal/fwa/2009/s394`
   - Exact citations: "FWA s.394" → `/au-federal/fwa/2009/s394`
   - Jurisdiction filtering (federal, victoria)
   - Returns ranked results

2. **get-legislation-content**
   - Text mode only (full statutory text)
   - Section filtering (e.g., s.394 only)
   - Local text file caching
   - Auto-download from legislation.gov.au and legislation.vic.gov.au
   - Integrity verification (SHA256 checksums)

3. **get-cache-status** (NEW)
   - Coverage metrics (P0: 100%, P1: 0%, etc.)
   - Cache size and freshness
   - Missing high-priority items
   - JSON output for monitoring

4. **CLI Admin Mode** (NEW)
   - `uv run mcp-fair-shake cache --priority P0` (pre-cache MVP)
   - `uv run mcp-fair-shake status` (check coverage)
   - `uv run mcp-fair-shake verify` (integrity check)
   - `uv run mcp-fair-shake update --all` (check for amendments)

**Data:**
- Raw text file: `data/legislation/cache/au-victoria/ohs-2004.txt`
- Metadata file: `data/legislation/cache/au-victoria/ohs-2004-metadata.json`
- Checksum file: `data/legislation/cache/au-victoria/ohs-2004.checksum`

### Deliverables

**Code:**
- [x] FastMCP server with tool registration (2025-12-23)
- [x] `resolve_legislation()` function (basic) (2025-12-23)
- [x] `get_legislation_content()` function (text mode) (2025-12-23)
- [x] Cache management module (2025-12-23)
- [x] Legislation fetcher (HTTP download) (2025-12-23)
- [x] Canonical ID parser/validator (2025-12-23)
- [x] Checksum verification (2025-12-23)

**Data:**
- [x] Data structure created (ready for caching) (2025-12-23)
- [x] Metadata tracking implemented (source URL, fetch date, checksum) (2025-12-23)
- [ ] OHS Act 2004 cached locally (requires manual pre-cache command)

**Tests:**
- [x] Test suite ≥80% coverage (83.54%) (2025-12-23)
- [x] Tool integration tests (2025-12-23)
- [x] Cache read/write tests (2025-12-23)
- [x] Checksum verification tests (2025-12-23)
- [x] Error handling tests (2025-12-23)

**Documentation:**
- [ ] README updated with Phase 1 usage
- [x] Tool descriptions in MCP schema (2025-12-23)
- [ ] Example queries documented

### Tasks

#### Week 1: Core Infrastructure

**Day 1-2: Project Setup**
- [x] Remove placeholder `evaluate` tool (2025-12-23)
- [x] Create `data/` directory structure (2025-12-23)
- [x] Implement canonical ID parser (2025-12-23)
  - Parse `/au-victoria/ohs/2004/s21`
  - Validate ID format
  - Extract jurisdiction, code, section
- [x] Implement cache module (2025-12-23)
  - Read/write text files
  - Load/save metadata
  - Check cache existence

**Day 3-4: Legislation Fetcher**
- [x] Research legislation.vic.gov.au API/scraping (2025-12-23)
- [x] Implement HTTP fetcher (2025-12-23)
  - Download legislation
  - Handle errors (network, 404, etc.)
  - Retry logic
- [x] Implement checksum generation (SHA256) (2025-12-23)
- [x] Implement metadata tracking (2025-12-23)
  - Source URL
  - Fetch timestamp
  - Content hash

**Day 5: Parsing & Indexing**
- [x] Parse legislation structure (basic) (2025-12-23)
  - Extract sections (simple pattern matching)
  - Basic section filtering
- [ ] Store parsed sections as JSON (deferred to Phase 2)
- [ ] Test with OHS Act 2004 (requires pre-caching)

#### Week 2: Tools & Testing

**Day 6-7: resolve-legislation Tool**
- [x] Implement basic citation matching (2025-12-23)
  - Natural language queries
  - Keyword matching
  - Jurisdiction filtering
- [x] Return canonical ID (2025-12-23)
- [x] Handle "not found" cases (2025-12-23)
- [x] Write unit tests (2025-12-23)

**Day 8-9: get-legislation-content Tool**
- [x] Implement content retrieval (2025-12-23)
  - Check cache first
  - Auto-download if missing
  - Return text content
- [x] Implement section filtering (basic) (2025-12-23)
  - Full Act vs. specific section
  - Simple pattern matching
- [x] Write integration tests (2025-12-23)

**Day 10: Quality & Polish**
- [x] Run full test suite (83.54% coverage) (2025-12-23)
- [x] Fix any failing tests (2025-12-23)
- [x] CLI admin mode implemented (2025-12-23)
- [ ] Update README with usage
- [x] Code review and refactor (2025-12-23)

### Success Criteria

- [x] All 3 tools functional (2025-12-23)
  - resolve-legislation ✓
  - get-legislation-content ✓
  - get-cache-status ✓
- [x] Test coverage ≥ 80% (83.54%) (2025-12-23)
- [x] Zero silent failures (2025-12-23)
- [x] Cache infrastructure complete (2025-12-23)
- [ ] OHS Act 2004 cached and queryable (requires manual pre-cache)
- [ ] Documentation complete (in progress)

### Risks & Mitigation

**Risk 1**: Legislation website structure changes
- *Mitigation*: Parse flexibly, log errors, manual fallback

**Risk 2**: Large file downloads slow
- *Mitigation*: Progress indicators, async downloads (Phase 2)

**Risk 3**: Section parsing incorrect
- *Mitigation*: Extensive fixtures, visual inspection, human review

---

## Phase 2: Victorian Coverage (Weeks 3-4)

**Goal**: Comprehensive Victorian workplace legislation

### Scope

**Add Legislation:**
- Equal Opportunity Act 2010
- Long Service Leave Act 2018
- Workers Compensation Act 1958
- Accident Compensation Act 1985
- Fair Work Act 2009 (Victoria-specific provisions)

**Enhance Tools:**
- Add `mode="summary"` (plain language)
- Add `mode="metadata"` (dates, amendments)
- Improve ranking algorithm
- Add jurisdiction filtering

**Data Improvements:**
- Convert to Parquet storage
- Implement update checks
- Build cross-reference index

### Tasks

**Week 3:**
- [ ] Fetch and cache 4 additional Victorian Acts
- [ ] Implement summary mode
  - Plain language summaries for key sections
  - Non-lawyer friendly explanations
- [ ] Implement metadata mode
  - Enactment/effective dates
  - Amendment history
  - Related provisions

**Week 4:**
- [ ] Parquet conversion
  - Export cached text to Parquet
  - Build query interface
  - Test performance vs. text files
- [ ] Cross-reference resolution
  - Parse citation patterns
  - Link related sections
  - Return related provisions
- [ ] Update checks
  - Track last update timestamp
  - Check for new versions
  - Log changes

### Success Criteria

- [x] 5+ Victorian Acts cached (2025-12-24)
- [ ] All 3 modes working (text, summary, metadata) - **DEFERRED to Phase 2.5**
- [ ] Parquet storage functional - **DEFERRED to Phase 2.5**
- [ ] Query performance < 500ms - **DEFERRED to Phase 2.5**

---

## Phase 2.5: Knowledge Graph Redesign 🔴 **CRITICAL - CURRENT PRIORITY**

**Goal**: Transform from unstructured text dump to state-of-the-art knowledge graph

**Status**: ⚪ Not Started
**Priority**: P0 (blocks all other phases)
**Timeline**: 3 weeks

### Problems with Current Implementation

1. **Output is Slop**
   - Navigation elements mixed with content
   - Table of contents collapsed into unreadable strings
   - Cannot retrieve specific sections (e.g., "Section 394")
   - No hierarchy: Act → Part → Division → Section → Subsection
   - No cross-references or relationships

2. **No Type Safety**
   - Functions return `str` or `dict[str, str]`
   - No validation, no IDE support
   - Easy to break contracts

3. **Monolithic Scraper**
   - All parsing in `fetcher.py`
   - Cannot extend for different sources
   - Violates Open/Closed Principle

### Scope

**Architecture Redesign:**
- ✅ Pydantic models for legislation structure (Act, Part, Division, Section, Subsection, Paragraph)
- ✅ Plugin-based parser architecture with dependency injection
- ✅ DuckDB knowledge graph for structured storage
- ✅ Web UI for graph visualization
- ✅ Type-safe MCP tools returning structured data

**See**: [ARCHITECTURE_REDESIGN.md](./ARCHITECTURE_REDESIGN.md) for complete technical specification

### Tasks

**Week 1: Pydantic Models & Parser Plugins**
- [ ] Define Pydantic models (`models/legislation.py`)
  - Act, Part, Division, Section, Subsection, Paragraph
  - CitationType enum
  - Cross-reference tracking
- [ ] Create parser protocol and registry
  - `LegislationParser` protocol
  - `ParserRegistry` for dependency injection
- [ ] Implement Federal HTML parser
  - Extract proper hierarchy from legislation.gov.au
  - Parse section numbers, titles, content
  - Extract cross-references
- [ ] Implement Victorian PDF parser
  - Parse structure from page markers
  - Extract section hierarchy
- [ ] Write comprehensive tests (80%+ coverage)

**Week 2: DuckDB Knowledge Graph**
- [ ] Design DuckDB schema
  - `nodes` table (id, type, content, metadata)
  - `edges` table (from_id, to_id, edge_type)
  - Full-text search index
- [ ] Implement `LegislationGraph` class
  - Insert Act with all children
  - Query by canonical ID
  - Full-text search
  - Citation graph traversal
- [ ] Migrate existing legislation to graph
  - Parse Fair Work Act into structure
  - Parse Victorian Acts into structure
  - Verify data integrity
- [ ] Performance testing
  - Query performance < 100ms
  - Graph export < 1s

**Week 3: Web UI Visualization**
- [ ] FastAPI server
  - `/` - Main graph visualization page
  - `/api/graph` - Export graph JSON
  - `/api/section/{id}` - Get section details
  - `/api/search?q=` - Full-text search
  - `/api/related/{id}` - Citation graph
- [ ] D3.js / Force-Graph visualization
  - Force-directed graph layout
  - Color-coded by type (Act, Part, Section)
  - Interactive node exploration
  - Click to see details
- [ ] Search and filter UI
  - Full-text search bar
  - Jurisdiction filter
  - Section type filter
- [ ] CLI command: `mcp-fair-shake serve`
  - Start web server on localhost:8000
  - Auto-open browser

### Success Criteria

- [ ] Can retrieve "Section 394 of Fair Work Act" with full hierarchy
- [ ] All Pydantic models validated with 100% type coverage
- [ ] Parsers use dependency injection (can add new without modifying core)
- [ ] DuckDB graph stores 17 Acts with cross-references
- [ ] Web UI visualizes knowledge graph
- [ ] Query "sections that cite Section 394" works
- [ ] Full-text search: "unfair dismissal" returns relevant sections
- [ ] All tests pass (111+ tests, 85%+ coverage)

### Migration Strategy

1. Build graph in parallel (don't delete existing cache)
2. Parse one Act at a time into structured format
3. Verify structured output matches original text
4. Update MCP tools to use graph
5. Deprecate text cache after verification

---

## Phase 2.5 Progress Update - Web UI Prototype (2025-12-27)

**Status**: 🟡 **Partial Complete** - Visualization working, data layer needs completion

### ✅ Completed (Week 3 Tasks)

**Frontend Visualization (Fully Functional)**
- ✅ FastAPI server with `/api/graph` endpoint (refactored from 205 to 64 lines)
- ✅ D3.js force-directed graph visualization
  - Color-coded by type (federal-act: blue, modern-award: green, state-act: amber, part: purple, division: pink, section: cyan)
  - Size hierarchy (acts > parts > divisions > sections)
  - Interactive node exploration with tooltips
  - Enhanced tooltips showing parent relationships and summaries
  - Zoom, pan, drag functionality
- ✅ Deck.gl 3D visualization
  - Type-based 3D spatial positioning
  - Same color/size encoding as 2D
  - Enhanced tooltips
  - Code complete (WebGL verification limited by Playwright environment)
- ✅ Port separation for human (8100/5273) vs agentic (8101/5274) development
- ✅ Frontend quality control: `make frontend-check` and `make frontend-test`

**Data Architecture**
- ✅ Created `data/legislation/graph/` directory structure
- ✅ JSON-based graph data storage (no hardcoding)
  - `top-level-acts.json` - 17 pieces of legislation
  - `fwa-2009-unfair-dismissal.json` - 13 detailed sections (Part 3-2)
- ✅ Shared data structure for both D3 and Deck.gl visualizations
- ✅ API loads from JSON files (clean separation of data and code)
- ✅ 16 pytest tests validating graph data structure (all passing)
  - No duplicate node IDs
  - All required fields present
  - Parent-child relationship consistency
  - Edge references validation

**Graph Coverage**
- ✅ 30 total nodes in knowledge graph:
  - 17 top-level acts (2 federal, 10 modern awards, 5 Victorian)
  - 13 hierarchical Fair Work Act nodes (1 part, 3 divisions, 9 sections)
- ✅ Demonstrates both breadth and depth ("finest granule" sample)

### ❌ Not Yet Complete (Week 1-2 Tasks)

**Data Layer - Still Manual**
- ❌ Pydantic models for legislation structure
- ❌ Plugin-based parser architecture
- ❌ Federal HTML parser (legislation.gov.au)
- ❌ Victorian PDF parser
- ❌ DuckDB knowledge graph storage
- ❌ Automated section extraction from cached legislation

**Current Limitation**: Graph data is manually curated in JSON files, not parsed from `data/legislation/cache/`. The visualization architecture is sound, but needs the parser infrastructure to automatically extract sections from legislation sources.

### Next Steps

1. **Implement Parsers** (Phase 2.5 Week 1-2):
   - Build Federal HTML parser to extract sections from Fair Work Act
   - Parse structure into JSON graph format
   - Migrate manual JSON to parser-generated data

2. **Complete DuckDB Integration** (Phase 2.5 Week 2):
   - Design schema for graph storage
   - Implement LegislationGraph class
   - Migrate from JSON files to DuckDB queries

3. **Add Search & Filter UI** (Phase 2.5 Week 3 remaining):
   - Full-text search bar
   - Jurisdiction filter
   - Section type filter
   - `/api/search` endpoint

### Architecture Validation

✅ **Proven Concepts:**
- JSON-based graph storage scales well (30 nodes, instant loading)
- pytest validation catches data errors early
- D3/Deck.gl handle hierarchical data beautifully
- API abstraction (load_graph_data) allows easy backend swaps

🎯 **Ready for Parser Integration:**
- Data structure validated and working
- Frontend accepts any valid graph JSON
- Adding parsers won't break existing visualizations

---

## Phase 3: Support Pathways (Weeks 5-6) 🟢

**Goal**: Map support agencies and resolution pathways

### Scope

**Implement `get-support` Tool:**
- Victorian support agencies
- Federal support agencies
- Step-by-step pathways
- Deadline tracking

**Agencies:**
- Fair Work Commission
- Fair Work Ombudsman
- WorkSafe Victoria
- Victorian Equal Opportunity & Human Rights Commission (VEOHRC)
- Community legal centers (Victoria)

**Pathways:**
- Unfair dismissal
- Wage theft / underpayment
- Workplace discrimination
- Bullying and harassment
- OHS incidents
- Workers' compensation claims

### Tasks

**Week 5: Agency Database**
- [ ] Research and compile agency info
  - Contact details (phone, email, website)
  - Services offered
  - Eligibility criteria
  - Costs (free, means-tested, paid)
  - Jurisdiction coverage
- [ ] Create JSON database structure
- [ ] Implement `get-support` tool
  - Match legislation to agencies
  - Filter by jurisdiction
  - Return contact info

**Week 6: Pathway Mapping**
- [ ] Design pathway JSON schema
- [ ] Document common scenarios
  - Unfair dismissal → FWC claim
  - Underpayment → FWO complaint
  - Discrimination → VEOHRC complaint
  - OHS incident → WorkSafe report
- [ ] Implement step-by-step guidance
- [ ] Add deadline tracking
  - 21 days for unfair dismissal
  - 6 months for general protections
  - Time limits for workers' comp
- [ ] Test and validate

### Success Criteria

- [ ] 10+ support agencies mapped
- [ ] 6+ common pathways documented
- [ ] Contact information verified
- [ ] Deadline tracking accurate
- [ ] Users can find support in ≤2 queries

---

## Phase 4: Federal Coverage (Weeks 7-9) 🟢

**Goal**: Add federal workplace legislation

### Scope

**Legislation:**
- ✅ Fair Work Act 2009 (complete)
- ✅ Fair Work Regulations 2009 (2025-12-24)
- ✅ Top 10 Modern Awards by employee coverage (2025-12-24)

**Features:**
- ✅ Jurisdiction filtering (federal vs. state)
- ✅ Conflict resolution (federal overrides state)
- ⚠️ Award lookup (basic - deferred to Phase 6)

### Tasks

**Week 7: Fair Work Act**
- [x] Fetch Fair Work Act 2009 (2025-12-24)
  - Source: legislation.gov.au
  - All sections, schedules
- [x] Cache and parse (2025-12-24)
- [x] Update resolution ranking (2025-12-24)
  - Prioritize federal for federal queries
  - Consider jurisdiction hierarchy

**Week 8: Regulations & Awards**
- [x] Fetch Fair Work Regulations 2009 (2025-12-24)
- [x] Research Modern Awards API/access (2025-12-24)
  - Found FWC PDF URLs: `https://www.fwc.gov.au/documents/modern_awards/pdf/ma{code}.pdf`
- [x] Fetch sample awards (2025-12-24)
  - MA000004: General Retail Industry Award 2020
  - MA000003: Fast Food Industry Award 2010
  - MA000009: Hospitality Industry (General) Award 2020
  - MA000018: Aged Care Award 2010
  - MA000022: Cleaning Services Award 2020
  - MA000005: Hair and Beauty Industry Award 2010
  - MA000034: Nurses Award 2020
  - MA000120: Children's Services Award 2020
  - MA000106: Real Estate Industry Award 2020
  - MA000002: Clerks - Private Sector Award 2020
- [ ] Implement award lookup (basic - deferred to Phase 6)

**Week 9: Federal Support**
- [x] Add FWC processes (2025-12-23 - via get-support tool)
- [x] Add FWO complaint pathways (2025-12-23 - via get-support tool)
- [x] Test federal + state coverage (2025-12-24)
- [x] Integration testing (2025-12-24 - 111 tests, 82.75% coverage)

### Success Criteria

- [x] Fair Work Act fully cached (2025-12-24)
- [x] Regulations accessible (2025-12-24)
- [x] Sample awards available (2025-12-24 - top 10 configured)
- [x] Federal/state filtering works (2025-12-24)
- [x] Support pathways include FWC/FWO (2025-12-23)

---

## Phase 5: National Coverage ⚪ **DEFERRED - LOWEST PRIORITY**

**Goal**: All Australian states and territories

**Status**: Deferred until after Phase 2.5 and Phase 6 complete
**Rationale**: Quality over quantity - perfect the small scope first

### Scope

**Legislation:**
- NSW, QLD, SA, WA, TAS, NT, ACT workplace legislation
- State-specific support agencies
- Automated update checks

### Tasks

**Weeks 10-13: State Legislation**
- [ ] Research each state's legislation sources
- [ ] Implement state-specific fetchers
  - NSW: legislation.nsw.gov.au
  - QLD: legislation.qld.gov.au
  - etc.
- [ ] Fetch key workplace Acts per state
  - WHS/OHS Acts
  - Workers' compensation
  - Equal opportunity
  - Industrial relations
- [ ] Update canonical ID for all jurisdictions

**Week 14: State Support**
- [ ] Research state agencies
  - WorkCover authorities
  - State tribunals
  - Legal aid (state-specific)
- [ ] Add to support database
- [ ] Map state-specific pathways

**Week 15: Automation**
- [ ] Implement weekly update checks
- [ ] Automated re-fetch if changed
- [ ] Update notification
- [ ] Data export capabilities
  - Export to CSV/JSON
  - Backup cached data
  - Integrity reports

### Success Criteria

- [ ] All 8 jurisdictions covered
- [ ] State agencies mapped
- [ ] Automated updates running
- [ ] Data export functional
- [ ] Offline operation supported

---

## Phase 6: Advanced Features (Future)

**Goal**: Enhanced search and analysis

### Scope (Not Time-Bound)

**DuckDB Integration:**
- [ ] Convert Parquet to DuckDB
- [ ] Complex SQL queries
- [ ] Aggregations and analytics
- [ ] Performance optimization

**Vector Embeddings:**
- [ ] Generate embeddings for sections
- [ ] Implement semantic search
- [ ] Similarity matching
- [ ] Natural language queries

**Smart Triggering:**
- [ ] Auto-detect legislation references
- [ ] Pattern matching for citations
- [ ] No explicit "use fair-shake" needed

**Advanced Features:**
- [ ] Historical versions (as-in-force dates)
- [ ] Case law integration
- [ ] Regulatory guidance lookup
- [ ] Conflict analysis
- [ ] Change tracking and notifications

### Tasks (To Be Planned)

**DuckDB:**
- [ ] Research DuckDB + Parquet integration
- [ ] Design database schema
- [ ] Implement query interface
- [ ] Benchmark performance

**Vector Embeddings:**
- [ ] Choose embedding model
- [ ] Generate embeddings for all cached legislation
- [ ] Implement vector search
- [ ] Integrate with resolve-legislation

**Natural Language:**
- [ ] Train/fine-tune citation detection
- [ ] Pattern matching library
- [ ] Auto-trigger on detected citations

---

## Dependencies & Blockers

### External Dependencies

1. **Government Websites**:
   - legislation.gov.au (federal)
   - legislation.vic.gov.au (Victoria)
   - State parliamentary sites (Phase 5)
   - **Risk**: API changes, site downtime
   - **Mitigation**: Flexible parsing, error handling, manual fallback

2. **Support Agency Information**:
   - FWC, FWO, WorkSafe, etc.
   - **Risk**: Contact info changes
   - **Mitigation**: Regular verification, update schedule

### Technical Blockers

1. **Parquet Library**:
   - Need: pandas or polars for Parquet
   - **Status**: Not yet added to dependencies
   - **Action**: Add in Phase 2

2. **DuckDB**:
   - Need: duckdb Python library
   - **Status**: Phase 6
   - **Action**: Research and plan separately

3. **Vector Embeddings**:
   - Need: sentence-transformers or similar
   - **Status**: Phase 6
   - **Action**: Research model selection

---

## Milestones & Demos

### Milestone 1: Phase 1 Complete (End of Week 2)
**Demo**: Query Victorian OHS Act via MCP
```
User: "use fair-shake: What are employer duties under OHS Act?"
→ resolve-legislation("OHS Act employer duties")
→ Returns: /au-victoria/ohs/2004/s21
→ get-legislation-content("/au-victoria/ohs/2004/s21", mode="text")
→ Returns: Full text of Section 21
```

### Milestone 2: Phase 2 Complete (End of Week 4)
**Demo**: Summary mode for Victorian legislation
```
User: "use fair-shake: Explain parental leave rights in Victoria"
→ resolve-legislation("parental leave victoria")
→ Returns: /au-victoria/lsl/2018/...
→ get-legislation-content(..., mode="summary")
→ Returns: Plain language explanation
```

### Milestone 3: Phase 3 Complete (End of Week 6)
**Demo**: Support pathway guidance
```
User: "use fair-shake: I think I was unfairly dismissed, what do I do?"
→ resolve-legislation("unfair dismissal")
→ Returns: /au-federal/fwa/2009/s394
→ get-support("/au-federal/fwa/2009/s394", situation="unfair dismissal")
→ Returns: Step-by-step FWC claim process, deadlines, contact info
```

### Milestone 4: Phase 4 Complete (End of Week 9)
**Demo**: Federal + state coverage
```
User: "use fair-shake: Compare federal and Victorian OHS requirements"
→ resolve-legislation("OHS requirements", jurisdiction="federal,victoria")
→ Returns: Both federal and state provisions
→ Cross-reference and compare
```

### Milestone 5: Phase 5 Complete (End of Week 15)
**Demo**: National coverage
```
User: "use fair-shake: What are casual employee rights in Queensland?"
→ resolve-legislation("casual employee rights", jurisdiction="queensland")
→ Returns: QLD-specific legislation + federal Fair Work Act
→ Comprehensive guidance covering both jurisdictions
```

---

## Resource Requirements

### Development Time

- **Phase 1**: 80 hours (2 weeks full-time)
- **Phase 2**: 80 hours (2 weeks full-time)
- **Phase 3**: 80 hours (2 weeks full-time)
- **Phase 4**: 120 hours (3 weeks full-time)
- **Phase 5**: 240 hours (6 weeks full-time)
- **Total (Phase 1-5)**: ~600 hours (~15 weeks)

### Storage Requirements

- **Phase 1**: ~5 MB (1 Act)
- **Phase 2**: ~25 MB (5 Acts)
- **Phase 3**: +10 MB (support pathways)
- **Phase 4**: +50 MB (federal legislation)
- **Phase 5**: +500 MB (all states)
- **Total**: ~600 MB

With Parquet compression (~40% reduction): ~360 MB

### Tools & Services

**Required:**
- uv (package management)
- FastMCP (MCP framework)
- pytest (testing)
- ruff, mypy (quality tools)

**Phase 2:**
- pandas or polars (Parquet)

**Phase 6:**
- DuckDB
- sentence-transformers (embeddings)
- Vector database (ChromaDB, FAISS, etc.)

---

## Success Metrics

### Phase 1 KPIs
- ✅ All tools functional
- ✅ Test coverage ≥ 80%
- ✅ Cache hit latency < 100ms
- ✅ Zero silent failures

### Phase 3 KPIs
- ✅ Support discovery ≤ 2 queries
- ✅ 90% of common scenarios covered
- ✅ Contact info verified

### Phase 5 KPIs
- ✅ National coverage complete
- ✅ Update automation running
- ✅ Offline operation functional
- ✅ 7-day data freshness

### Phase 6 KPIs
- ✅ Semantic search accuracy ≥ 90%
- ✅ Complex queries resolved
- ✅ Historical version tracking

---

## Review & Adaptation

### Weekly Reviews
- Review progress vs. plan
- Adjust timelines if needed
- Identify blockers
- Update roadmap

### Phase Gates
Each phase requires:
1. Success criteria met
2. Test coverage maintained
3. Documentation updated
4. User feedback incorporated (if available)

Only proceed to next phase when current phase is complete.

---

## Long-Term Vision (Post-Phase 6)

**Potential Future Enhancements:**
- AI-powered case outcome prediction
- Automated legal form generation
- Integration with union systems
- Employer-facing compliance tools
- Mobile app with voice search
- Multilingual support (CALD communities)
- Integration with existing legal aid systems

**Sustainability:**
- Community contributions
- Partnership with unions/legal aid
- Potential grant funding
- Maintenance and update schedule

---

**Last Updated**: 2025-12-23
**Next Review**: End of Phase 1 (Week 2)
