# MCP Fair Shake - Requirements Document

**Version:** 1.0
**Last Updated:** 2025-12-23
**Status:** Planning Phase

## Project Vision

**MCP Fair Shake** is a Model Context Protocol server that provides authoritative, unbiased access to Australian workplace legislation and support pathways.

### Core Mission

**Reduce the cost of having timely, grounded, and factual legislation and support pathways in the hands of employees via AI chat assistants and this MCP.**

This is a warning to dodgy and unscrupulous employers: **employees are now more empowered than ever**, and employers will be held accountable via the right and legal pathways that exist and may be underutilized.

The system empowers employees—often the disenfranchised party in workplace disputes—to:
- Understand their rights with authoritative, up-to-date legislation
- Access support services through clear pathways
- Navigate legal frameworks when employers exploit grey areas
- Act swiftly with deadline-aware guidance
- Access this information at near-zero cost through AI assistants

## Core Principles

1. **Employee-First**: Prioritize the needs of employees who lack resources for legal research and representation
2. **Fair & Balanced**: Interpret legislation objectively, fairly representing both employer and employee perspectives
3. **Authoritative**: Use only official government sources for legislation text
4. **Actionable**: Provide clear next steps and support pathways, not just legal text
5. **Accessible**: Plain language summaries alongside technical legal text
6. **Local First**: Cache legislation locally for fast, reliable access

## Scope

### Geographic Coverage

**Phase 1 (MVP - Federal + Victorian):**
- **Federal workplace legislation**: Fair Work Act 2009 (complete focus on unfair dismissal)
- **Victorian state legislation**: Occupational Health and Safety Act 2004, Equal Opportunity Act 2010

**Phased National Rollout:**
- **Phase 2-4**: Expand federal coverage (regulations, modern awards)
- **Phase 5+**: All Australian states and territories:
  - New South Wales (NSW)
  - Queensland (QLD)
  - South Australia (SA)
  - Western Australia (WA)
  - Tasmania (TAS)
  - Northern Territory (NT)
  - Australian Capital Territory (ACT)

### Initial Focus Area

**Unfair Dismissal** - The first and primary use case:
- Fair Work Act 2009, Part 3-2 (Division 2-4)
- Key sections: s.385-398 (unfair dismissal provisions)
- FWC claim processes and deadlines (21 days)
- Support pathways (Fair Work Commission, Fair Work Ombudsman)
- Eligibility criteria and remedy options

This focus area drives the initial implementation and validates the entire system architecture.

### Legislative Focus

**Workplace Legislation:**
- Employment contracts and agreements
- Workplace health and safety (WHS/OHS)
- Fair Work Act and regulations
- Modern Awards and Enterprise Agreements
- Discrimination and equal opportunity
- Workers' compensation
- Superannuation obligations
- Leave entitlements (annual, sick, parental, etc.)
- Termination and redundancy
- Workplace bullying and harassment
- Wage theft and underpayment

**Support Frameworks:**
- Fair Work Commission procedures
- Fair Work Ombudsman pathways
- State workplace tribunals
- Legal aid services
- Union support services
- Community legal centers
- Worker advocacy organizations
- Complaint and dispute resolution processes

## Functional Requirements

### FR-1: Legislation Resolution

**Tool:** `resolve-legislation`

**Requirements:**
- FR-1.1: Accept natural language legislation queries (e.g., "unfair dismissal", "casual employee rights")
- FR-1.2: Accept formal citations (e.g., "Fair Work Act 2009 s.394")
- FR-1.3: Rank results by:
  - Citation accuracy (exact matches prioritized)
  - Jurisdiction match (federal vs. state)
  - Currency (current vs. historical versions)
  - Authority level (primary legislation > regulations > guidance)
  - Relevance to query intent
- FR-1.4: Return canonical legislation IDs
- FR-1.5: Handle ambiguous queries with clarifying questions
- FR-1.6: Support both federal and state jurisdiction filtering

### FR-2: Legislation Content Retrieval

**Tool:** `get-legislation-content`

**Requirements:**
- FR-2.1: Fetch content by canonical legislation ID
- FR-2.2: Support three content modes:
  - `mode="text"`: Full statutory text with official citations and cross-references
  - `mode="summary"`: Plain language summaries accessible to non-lawyers
  - `mode="metadata"`: Enactment dates, amendments, related regulations, case law
- FR-2.3: Support section/subsection filtering
- FR-2.4: Implement pagination for long statutes (pages 1-10)
- FR-2.5: Include effective dates and amendment history
- FR-2.6: Provide cross-references to related provisions
- FR-2.7: Handle historical versions (as-in-force dates)

### FR-3: Support Pathway Navigation

**Tool:** `get-support` (or `next-steps`)

**Requirements:**
- FR-3.1: Map support agencies to relevant legislation
- FR-3.2: Provide contact information for support services:
  - Fair Work Commission
  - Fair Work Ombudsman
  - State workplace tribunals
  - Legal aid services (state-specific)
  - Community legal centers
  - Unions and worker organizations
  - Worker advocacy groups
- FR-3.3: Outline complaint and dispute resolution processes
- FR-3.4: Provide step-by-step guidance for common situations:
  - Unfair dismissal claims
  - Underpayment recovery
  - Workplace discrimination complaints
  - Bullying and harassment reports
  - WHS incident reporting
- FR-3.5: Include eligibility criteria for support services
- FR-3.6: Estimate timeframes for resolution pathways
- FR-3.7: Identify free vs. paid support options
- FR-3.8: Provide jurisdiction-specific guidance (federal vs. state pathways)

### FR-4: Explicit Triggering

**Requirements:**
- FR-4.1: Require explicit "use fair-shake" trigger phrase in queries
- FR-4.2: Respond to variations: "use fair shake", "fairshake", etc.
- FR-4.3: Provide clear error messages when trigger is missing
- FR-4.4: Document trigger requirement in tool descriptions

### FR-5: Local Data Management

**Requirements:**
- FR-5.1: Fetch legislation from official government sources:
  - Federal Register of Legislation (legislation.gov.au)
  - Victorian Legislation and Parliamentary Documents
  - State parliamentary websites for other jurisdictions
- FR-5.2: Cache legislation locally in structured format:
  - Raw text files (human-readable, version-controlled)
  - Compressed Parquet files (efficient querying)
- FR-5.3: Store metadata separately:
  - Source URLs
  - Fetch dates
  - Hash checksums for integrity verification
  - Amendment history
- FR-5.4: Implement incremental updates (fetch only changed content)
- FR-5.5: Provide data export capabilities for transparency
- FR-5.6: Support offline operation after initial data fetch

## Non-Functional Requirements

### NFR-1: Performance
- NFR-1.1: Legislation lookup < 500ms (cached)
- NFR-1.2: Support resolution < 2 seconds (first query)
- NFR-1.3: Handle concurrent requests (5+ simultaneous users)

### NFR-2: Data Quality
- NFR-2.1: Use only official government sources
- NFR-2.2: Verify content integrity with checksums
- NFR-2.3: Track data freshness (last update timestamps)
- NFR-2.4: Implement automated update checks (weekly)

### NFR-3: Reliability
- NFR-3.1: Graceful degradation if external sources unavailable
- NFR-3.2: Fail loudly for data integrity issues (no silent failures)
- NFR-3.3: Comprehensive error logging
- NFR-3.4: Data redundancy (backup cached data)

### NFR-4: Maintainability
- NFR-4.1: Well-documented code (docstrings, type hints)
- NFR-4.2: Comprehensive test coverage (≥80%)
- NFR-4.3: Clear separation of concerns (data layer, business logic, API)
- NFR-4.4: Version control for cached legislation

### NFR-5: Transparency
- NFR-5.1: Clear source attribution for all content
- NFR-5.2: Visible fetch dates and version information
- NFR-5.3: Plain language explanations of legal concepts
- NFR-5.4: Disclaimer that tool is informational, not legal advice

## Data Architecture

### Canonical ID Format

```
/{jurisdiction}/{code-type}/{act-code}/{section?}/{subsection?}

Examples:
/au-federal/fwa/2009/s394                    # Fair Work Act 2009, Section 394
/au-victoria/ohs/2004/s21                    # OHS Act 2004 (VIC), Section 21
/au-federal/fwr/2009/reg3.1                  # Fair Work Regulations, Regulation 3.1
/au-nsw/ira/1996/s106                        # Industrial Relations Act 1996 (NSW)
```

### Data Storage Structure

```
data/
├── legislation/
│   ├── raw/                                 # Human-readable text files
│   │   ├── au-federal/
│   │   │   ├── fwa-2009.txt
│   │   │   ├── fwr-2009.txt
│   │   │   └── metadata.json
│   │   └── au-victoria/
│   │       ├── ohs-2004.txt
│   │       ├── eoa-2010.txt
│   │       └── metadata.json
│   └── parquet/                             # Compressed, queryable format
│       ├── legislation.parquet
│       ├── sections.parquet
│       └── citations.parquet
├── support-pathways/
│   ├── federal-agencies.json
│   ├── victoria-agencies.json
│   └── [state]-agencies.json
└── cache/
    └── checksums.json                       # Content integrity verification
```

### Database Schema (Future: DuckDB)

```sql
-- Legislation table
CREATE TABLE legislation (
    canonical_id VARCHAR PRIMARY KEY,
    jurisdiction VARCHAR NOT NULL,
    code_type VARCHAR NOT NULL,
    short_name VARCHAR,
    full_name VARCHAR NOT NULL,
    enactment_date DATE,
    effective_date DATE,
    current_version BOOLEAN,
    source_url VARCHAR,
    fetch_date TIMESTAMP,
    checksum VARCHAR
);

-- Sections table
CREATE TABLE sections (
    section_id VARCHAR PRIMARY KEY,
    legislation_id VARCHAR REFERENCES legislation(canonical_id),
    section_number VARCHAR,
    title VARCHAR,
    text TEXT,
    effective_date DATE,
    amended_by VARCHAR[],
    cross_references VARCHAR[]
);

-- Support pathways table
CREATE TABLE support_pathways (
    pathway_id VARCHAR PRIMARY KEY,
    agency_name VARCHAR NOT NULL,
    jurisdiction VARCHAR,
    contact_phone VARCHAR,
    contact_email VARCHAR,
    website VARCHAR,
    services TEXT[],
    eligibility_criteria TEXT,
    cost VARCHAR,  -- 'free', 'means-tested', 'paid'
    relevant_legislation VARCHAR[]
);

-- Citations table (for resolution)
CREATE TABLE citations (
    citation_id VARCHAR PRIMARY KEY,
    section_id VARCHAR REFERENCES sections(section_id),
    citation_format VARCHAR,  -- e.g., "FWA s.394", "Fair Work Act 2009, s.394"
    citation_type VARCHAR     -- 'official', 'popular', 'acronym'
);
```

## Pre-Caching Strategy & Coverage Estimation

### Caching Modes

The system supports two caching approaches:

**1. Cache-On-Demand** (Default for MVP):
- Legislation fetched when first requested
- Background download if not cached
- User waits only on first query (~3-5 seconds)
- Subsequent queries instant (< 100ms)

**2. Pre-Cache Complete Database** (Admin/CLI Mode):
- Batch download all target legislation
- Run as background process or CLI command
- Progress tracking and status reporting
- Enables fully offline operation

### Complete Coverage Definition

**"Complete"** means caching all workplace-relevant legislation for target jurisdictions:

#### Federal Legislation (Complete Coverage)
| Legislation | Size Estimate | Sections | Priority |
|------------|---------------|----------|----------|
| Fair Work Act 2009 | ~2.5 MB | 789 sections | **P0** (MVP) |
| Fair Work Regulations 2009 | ~800 KB | ~350 regulations | P1 |
| Top 20 Modern Awards | ~15 MB | Varies | P1 |
| Other Modern Awards (~100) | ~75 MB | Varies | P2 |
| Work Health and Safety Act 2011 | ~600 KB | 274 sections | P1 |
| WHS Regulations | ~1.2 MB | ~500 regulations | P1 |
| Age Discrimination Act 2004 | ~200 KB | 52 sections | P2 |
| Disability Discrimination Act 1992 | ~400 KB | 122 sections | P2 |
| Racial Discrimination Act 1975 | ~250 KB | 43 sections | P2 |
| Sex Discrimination Act 1984 | ~500 KB | 142 sections | P2 |
| **Federal Total** | **~97 MB** | **~3000+ items** | |

#### Victorian Legislation (Complete Coverage)
| Legislation | Size Estimate | Sections | Priority |
|------------|---------------|----------|----------|
| Occupational Health and Safety Act 2004 | ~500 KB | 157 sections | **P0** (MVP) |
| Equal Opportunity Act 2010 | ~350 KB | 128 sections | **P0** (MVP) |
| Long Service Leave Act 2018 | ~200 KB | 61 sections | P1 |
| Workers Compensation Act 1958 | ~1.5 MB | 300+ sections | P1 |
| Accident Compensation Act 1985 | ~2 MB | 450+ sections | P1 |
| Charter of Human Rights 2006 | ~150 KB | 43 sections | P2 |
| Owner Drivers and Forestry Contractors Act 2005 | ~180 KB | 58 sections | P2 |
| **Victorian Total** | **~5 MB** | **~1200+ items** | |

#### Other States (Phase 5+)
| State | Est. Workplace Acts | Size Estimate | Priority |
|-------|-------------------|---------------|----------|
| NSW | 15-20 Acts | ~20 MB | P3 |
| QLD | 15-20 Acts | ~18 MB | P3 |
| SA | 12-15 Acts | ~15 MB | P3 |
| WA | 12-15 Acts | ~16 MB | P3 |
| TAS | 10-12 Acts | ~12 MB | P3 |
| NT | 8-10 Acts | ~10 MB | P3 |
| ACT | 8-10 Acts | ~9 MB | P3 |
| **Other States Total** | **~100 Acts** | **~100 MB** | |

#### Support Pathways Data
| Data Type | Size Estimate | Items | Priority |
|-----------|---------------|-------|----------|
| Federal agencies | ~50 KB | 5-10 agencies | P0 |
| Victorian agencies | ~50 KB | 10-15 agencies | P0 |
| Other state agencies | ~300 KB | 50-70 agencies | P3 |
| Pathway templates | ~200 KB | 20-30 pathways | P0-P1 |
| **Support Data Total** | **~600 KB** | **~100 items** | |

### Total Database Size Estimates

| Coverage Level | Raw Text | Parquet (60% compression) | Priority |
|---------------|----------|--------------------------|----------|
| **MVP (P0)** | ~4 MB | ~2.4 MB | **Phase 1** |
| **Phase 1-2 Complete** | ~20 MB | ~12 MB | **Phase 2** |
| **Federal + Victoria (P0-P1)** | ~100 MB | ~60 MB | **Phase 3-4** |
| **National Complete (P0-P3)** | ~200 MB | ~120 MB | **Phase 5** |
| **Full Coverage (All Priorities)** | ~500 MB | ~300 MB | **Phase 6** |

### Progress Tracking

#### FR-6: Status and Progress Tool

**New Tool:** `get-cache-status`

```python
def get_cache_status() -> str:
    """Get caching progress and coverage statistics.

    Returns:
        JSON with coverage metrics:
        {
            "coverage": {
                "federal": {
                    "total_acts": 10,
                    "cached_acts": 2,
                    "percentage": 20.0,
                    "size_mb": 3.2
                },
                "victoria": {
                    "total_acts": 7,
                    "cached_acts": 2,
                    "percentage": 28.6,
                    "size_mb": 0.85
                },
                "total": {
                    "total_acts": 17,
                    "cached_acts": 4,
                    "percentage": 23.5,
                    "size_mb": 4.05
                }
            },
            "priorities": {
                "P0": {"cached": 2, "total": 3, "percentage": 66.7},
                "P1": {"cached": 2, "total": 8, "percentage": 25.0},
                "P2": {"cached": 0, "total": 6, "percentage": 0.0}
            },
            "freshness": {
                "oldest_cache": "2025-11-15T10:30:00Z",
                "newest_cache": "2025-12-23T14:20:00Z",
                "needs_update": 0
            },
            "storage": {
                "cache_dir": "data/legislation/cache/",
                "total_size_mb": 4.05,
                "available_space_mb": 45123.5
            }
        }
    """
```

#### CLI Admin Mode

**New Requirement:** CLI commands for pre-caching and maintenance

```bash
# Pre-cache all P0 (MVP) legislation
uv run mcp-fair-shake cache --priority P0

# Pre-cache specific jurisdiction
uv run mcp-fair-shake cache --jurisdiction federal

# Pre-cache specific legislation
uv run mcp-fair-shake cache --id /au-federal/fwa/2009

# Check cache status
uv run mcp-fair-shake status

# Verify cache integrity
uv run mcp-fair-shake verify

# Update cached legislation (check for amendments)
uv run mcp-fair-shake update --all

# Export cache inventory
uv run mcp-fair-shake export --format json
```

#### Progress Metrics

Track and report:
- **Coverage percentage** by jurisdiction
- **Coverage percentage** by priority (P0, P1, P2, P3)
- **Total cached size** vs. estimated complete size
- **Freshness** (oldest cache, newest cache, update needed)
- **Integrity** (checksum verification pass/fail)
- **Completeness** (missing high-priority items)

#### Coverage Milestones

| Milestone | Coverage | Size | Status |
|-----------|----------|------|--------|
| **MVP Ready** | P0 complete (4 Acts) | ~4 MB | 🔵 Target |
| **Phase 2 Ready** | P0-P1 federal + VIC | ~100 MB | ⚪ Future |
| **Production Ready** | Federal + VIC complete | ~100 MB | ⚪ Future |
| **National Complete** | All P0-P2 | ~200 MB | ⚪ Future |
| **Full Coverage** | All priorities | ~500 MB | ⚪ Future |

## Phased Implementation

### Phase 1: MVP (Minimum Viable Product)
**Timeline:** Sprint 1-3 (3 weeks)
**Goal:** Unfair dismissal use case with federal + Victorian legislation

**Primary Use Case: Unfair Dismissal**
- Fair Work Act 2009, Part 3-2 (unfair dismissal provisions)
- FWC claim process and 21-day deadline
- Eligibility criteria and remedy options

**Legislation Coverage (P0 Priority):**
- ✅ Fair Work Act 2009 (federal) - Focus on unfair dismissal sections
- ✅ Victorian OHS Act 2004
- ✅ Victorian Equal Opportunity Act 2010

**Deliverables:**
- ✅ Three-tool pattern: `resolve-legislation`, `get-legislation-content`, `get-cache-status`
- ✅ Unfair dismissal sections (FWA s.385-398) fully cached and queryable
- ✅ Text mode only (no summaries yet)
- ✅ Explicit "use fair-shake" trigger
- ✅ Local text file caching with integrity verification
- ✅ Citation matching for unfair dismissal queries
- ✅ CLI admin mode for pre-caching
- ✅ Test suite with ≥80% coverage
- ✅ TDD workflow established

### Phase 2: Victorian Coverage
**Timeline:** Sprint 3-4
**Goal:** Comprehensive Victorian workplace legislation

**Deliverables:**
- ✅ All Victorian workplace legislation:
  - Equal Opportunity Act 2010
  - Long Service Leave Act 2018
  - Workers Compensation legislation
- ✅ Summary mode (plain language)
- ✅ Metadata mode (dates, amendments)
- ✅ Section/subsection filtering
- ✅ Cross-reference support
- ✅ Parquet storage for efficient querying

### Phase 3: Support Pathways
**Timeline:** Sprint 5-6
**Goal:** Map support agencies and resolution pathways

**Deliverables:**
- ✅ `get-support` tool implementation
- ✅ Victorian support agency database:
  - Fair Work Commission
  - Fair Work Ombudsman
  - WorkSafe Victoria
  - Victorian Equal Opportunity and Human Rights Commission
  - Community legal centers
- ✅ Step-by-step guidance for common scenarios
- ✅ Eligibility criteria and cost information

### Phase 4: Federal Coverage
**Timeline:** Sprint 7-9
**Goal:** Add federal workplace legislation

**Deliverables:**
- ✅ Fair Work Act 2009 (complete)
- ✅ Fair Work Regulations 2009
- ✅ Federal support pathways
- ✅ Jurisdiction filtering (federal vs. state)
- ✅ Conflict resolution (federal overrides state)
- ✅ Modern Awards and Enterprise Agreements (sample)

### Phase 5: National Coverage
**Timeline:** Sprint 10-15
**Goal:** All Australian states and territories

**Deliverables:**
- ✅ NSW, QLD, SA, WA, TAS, NT, ACT legislation
- ✅ State-specific support agencies
- ✅ Automated update checks
- ✅ Data export capabilities

### Phase 6: Advanced Features (Future)
**Timeline:** TBD
**Goal:** Enhanced search and analysis capabilities

**Deliverables:**
- ✅ DuckDB integration for complex queries
- ✅ Vector embeddings for semantic search
- ✅ Natural language query understanding (no explicit trigger)
- ✅ Case law integration
- ✅ Regulatory guidance lookup
- ✅ Conflict analysis tools
- ✅ Historical version tracking (as-in-force dates)

## Success Criteria

### Phase 1 Success Metrics:
- [ ] 100% of test queries return correct Victorian OHS Act sections
- [ ] Legislation lookup < 500ms (cached)
- [ ] Test coverage ≥ 80%
- [ ] Zero silent failures (all errors logged and reported)

### Phase 3 Success Metrics:
- [ ] Users can find relevant support agencies in ≤2 queries
- [ ] Support pathways cover 90% of common workplace disputes
- [ ] Contact information verified and current

### Phase 6 Success Metrics:
- [ ] Semantic search accuracy ≥ 90% (finds relevant legislation without exact citations)
- [ ] Complex queries (multi-jurisdiction, cross-references) resolved correctly
- [ ] Offline operation supported with 7-day data freshness

## Implementation Methodology

### Test-Driven Development (TDD) Workflow

**All feature development MUST follow this workflow:**

#### 1. Write Tests First
```python
# Example: Test for resolve-legislation with unfair dismissal query
def test_resolve_unfair_dismissal():
    """Test resolving 'unfair dismissal' query to FWA s.394."""
    result = resolve_legislation("unfair dismissal")

    assert len(result) > 0
    assert result[0]["canonical_id"] == "/au-federal/fwa/2009/s394"
    assert result[0]["confidence"] >= 0.9
    assert "unfair dismissal" in result[0]["title"].lower()
```

- Write test cases BEFORE implementing the feature
- Cover happy path, edge cases, and error conditions
- Use parametrized tests for multiple scenarios
- Aim for ≥80% coverage (target: 90%+ for critical paths)

#### 2. Implement Feature
- Implement ONLY enough code to make tests pass
- Follow YAGNI (You Aren't Gonna Need It)
- Keep complexity low (< 150k output tokens per feature)
- Use type hints and docstrings
- Log errors explicitly (fail loudly)

#### 3. Verify Tests Pass
```bash
# Run tests for the specific feature
uv run pytest tests/test_resolve.py::test_resolve_unfair_dismissal -v

# Verify all tests still pass
uv run pytest -v
```

- All new tests must pass
- No regression (existing tests must still pass)
- Test output should be clean (no warnings/errors)

#### 4. Ensure Quality Standards
```bash
# Run full quality check pipeline
make check

# This runs:
# - ruff format (code formatting)
# - ruff check (linting)
# - mypy (type checking)
# - pytest with ≥80% coverage
```

- `make check` must pass completely
- `make test` must pass completely
- Zero linting errors
- Zero type errors
- Coverage ≥ 80%

#### 5. Review and Refactor
- Review code for unnecessary complexity
- Refactor if complexity is high
- Keep functions small and focused
- Extract reusable components
- Update docstrings and type hints
- Re-run `make check` after refactoring

### Feature Complexity Guidelines

**Each feature should be small enough for agentic completion:**

**Target**: < 150k output tokens per feature (~30-50 KB of code)

**Good Feature Scope** (can be completed in one shot):
- ✅ "Implement canonical ID parser"
- ✅ "Add checksum verification for cached files"
- ✅ "Implement citation matching for FWA sections"
- ✅ "Add unfair dismissal query ranking"

**Too Large** (needs breaking down):
- ❌ "Implement entire resolve-legislation tool"
- ❌ "Build complete caching system"
- ❌ "Add all Victorian legislation"

**Feature Decomposition Example:**

Large Feature: "Implement resolve-legislation tool"

Break into:
1. Feature: Canonical ID parser (parse/validate IDs)
2. Feature: Basic citation matcher (exact citations only)
3. Feature: Fuzzy query matcher (natural language)
4. Feature: Result ranking algorithm
5. Feature: Jurisdiction filtering
6. Feature: Historical version support

Each sub-feature follows full TDD workflow independently.

### Complexity Management

**Keep code complexity low:**
- **Cyclomatic complexity** < 10 per function
- **Function length** < 50 lines (prefer < 30)
- **Module size** < 500 lines
- **Nesting depth** < 4 levels

**Refactoring Triggers:**
- Function > 50 lines → Extract sub-functions
- Module > 500 lines → Split into sub-modules
- Duplicate code (3+ times) → Extract to helper
- Complex conditionals → Use lookup tables or polymorphism

**Continuous Refactoring:**
- After each feature, review whole codebase
- Look for patterns that could be simplified
- Keep abstractions minimal (avoid over-engineering)
- Prefer explicit over clever

## Constraints & Assumptions

### Constraints:
- Must use official government sources only (no third-party summaries)
- Must maintain data integrity (checksums, version control)
- Must fail loudly on data issues (no silent failures)
- Must include disclaimer (informational only, not legal advice)

### Assumptions:
- Government legislation websites remain accessible and stable
- Legislation text is available in machine-readable format (HTML, XML, or JSON)
- Users have internet connectivity for initial data fetch
- Users understand this is informational, not a replacement for legal counsel

## Out of Scope (Explicitly Excluded)

- ❌ Legal advice or case-specific recommendations
- ❌ Document generation (contracts, complaints, etc.)
- ❌ Automated legal form filling
- ❌ Representation or advocacy services
- ❌ Non-workplace legislation (criminal, family law, etc.)
- ❌ International law (except as it relates to Australian workplace law)
- ❌ Paid services or monetization features

## References

- [Federal Register of Legislation](https://www.legislation.gov.au/)
- [Victorian Legislation and Parliamentary Documents](https://www.legislation.vic.gov.au/)
- [Fair Work Commission](https://www.fwc.gov.au/)
- [Fair Work Ombudsman](https://www.fairwork.gov.au/)
- [WorkSafe Victoria](https://www.worksafe.vic.gov.au/)
- [Context7 MCP Analysis](./context7-analysis.md)
