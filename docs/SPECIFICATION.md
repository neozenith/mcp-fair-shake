# MCP Fair Shake - Technical Specification

**Version:** 1.0
**Last Updated:** 2025-12-23
**Status:** Design Phase

## 1. System Overview

### 1.1 Purpose

MCP Fair Shake is a Model Context Protocol server that provides authoritative access to Australian workplace legislation and support pathways. The system combines:
- **Context7's two-step resolution pattern** for precise legislation lookup
- **arXiv's local-first caching strategy** for fast, reliable access
- **Custom support pathway tool** for actionable employee guidance

### 1.2 Architecture Principles

1. **Local-First**: Cache legislation locally for speed and offline capability
2. **Explicit Triggering**: Require "use fair-shake" phrase (Phase 1)
3. **Fail Loudly**: No silent failures; log and report all errors
4. **Authoritative Sources**: Official government websites only
5. **Data Integrity**: Checksums and version control for all cached content
6. **Separation of Concerns**: Resolution → Content → Support (distinct responsibilities)

### 1.3 Design Patterns

**From Context7:**
- Two-step resolution (resolve → get-content)
- Mode parameter for content types
- Ranked result selection
- Canonical ID format

**From arXiv:**
- Local caching with metadata tracking
- Structured filtering (jurisdiction, date, category)
- Background downloads
- Inventory management

**Unique to Legislation:**
- Support pathway mapping
- Jurisdiction hierarchy (federal > state > local)
- Amendment tracking with effective dates
- Cross-reference resolution

## 2. Tool Specifications

### 2.1 Tool: resolve-legislation

**Purpose**: Resolve natural language or citation queries to canonical legislation IDs

#### Parameters

```python
def resolve_legislation(
    query: str,
    jurisdiction: str = "all",
    date: str | None = None
) -> str:
    """Resolve legislation reference to canonical ID.

    Args:
        query: Natural language or citation
            Examples:
            - "unfair dismissal"
            - "casual employee rights"
            - "Fair Work Act section 394"
            - "FWA 2009 s.394"
            - "OHS Act Victoria"

        jurisdiction: Filter results by jurisdiction
            Options:
            - "all" (default - search all jurisdictions)
            - "federal" (Commonwealth legislation only)
            - "victoria", "nsw", "qld", etc. (state-specific)
            - Can combine: "federal,victoria"

        date: As-in-force date (ISO format "YYYY-MM-DD")
            - None (default): Current version
            - "2020-01-15": Version in force on that date
            - Enables historical version lookup

    Returns:
        JSON array of matching legislation, ranked by relevance:
        [
            {
                "canonical_id": "/au-federal/fwa/2009/s394",
                "short_name": "FWA s.394",
                "full_name": "Fair Work Act 2009, Section 394",
                "title": "Meaning of unfair dismissal",
                "jurisdiction": "federal",
                "authority_level": "primary_legislation",
                "confidence": 0.95,
                "match_reason": "Exact citation match"
            },
            {...}
        ]

    Raises:
        ValueError: If query is empty or invalid
        LookupError: If no matches found (with suggestions)
    """
```

#### Ranking Algorithm

Results ranked by weighted score:

1. **Citation Accuracy** (40%):
   - Exact citation format match: 1.0
   - Partial citation match: 0.7
   - Section number match: 0.5
   - Name match only: 0.3

2. **Jurisdiction Match** (25%):
   - Exact match: 1.0
   - Hierarchically related (federal for state query): 0.6
   - Different jurisdiction: 0.2

3. **Currency** (20%):
   - Current version: 1.0
   - Recent amendment (<1 year): 0.9
   - Historical version: 0.5
   - Repealed legislation: 0.1

4. **Authority Level** (10%):
   - Constitutional: 1.0
   - Primary legislation (Acts): 0.9
   - Regulations: 0.7
   - Administrative guidance: 0.5

5. **Semantic Relevance** (5%):
   - Query terms in title: 1.0
   - Query terms in section text: 0.7
   - Related provisions: 0.4

**Final Score** = Σ(factor × weight)

Results sorted descending, top 5 returned.

#### Example Queries

```
Query: "unfair dismissal"
Jurisdiction: "all"
Date: None

Returns:
[
    {canonical_id: "/au-federal/fwa/2009/s394", confidence: 0.92},
    {canonical_id: "/au-federal/fwa/2009/s385", confidence: 0.85},
    {canonical_id: "/au-victoria/fwa-guide/unfair-dismissal", confidence: 0.65}
]
```

```
Query: "FWA 2009 s.394"
Jurisdiction: "federal"
Date: "2015-07-01"

Returns:
[
    {canonical_id: "/au-federal/fwa/2009/s394",
     version: "2015-07-01",
     confidence: 1.0,
     match_reason: "Exact citation + date match"}
]
```

### 2.2 Tool: get-legislation-content

**Purpose**: Fetch legislation content from local cache (auto-download if needed)

#### Parameters

```python
def get_legislation_content(
    canonical_id: str,
    section: str = "",
    mode: Literal["text", "summary", "metadata"] = "summary",
    page: int = 1
) -> str:
    """Fetch legislation content.

    Args:
        canonical_id: Canonical ID from resolve-legislation
            Format: /{jurisdiction}/{code-type}/{code}/{section?}
            Example: "/au-federal/fwa/2009/s394"

        section: Focus on specific section/subsection (optional)
            Examples:
            - "" (empty): Entire legislation/section from canonical_id
            - "3": Subsection 3
            - "3.2.a": Nested subsection
            - "Schedule 1": Specific schedule

        mode: Content type
            - "text": Full statutory text with citations
                * Official legislative text
                * Cross-references to related provisions
                * Footnotes and annotations
                * Amendment history inline

            - "summary": Plain language summary
                * Written for non-lawyers
                * Key provisions explained
                * Practical examples
                * Related rights/obligations

            - "metadata": Legislation details
                * Enactment date, effective date
                * Amendment history (dates, bills)
                * Related regulations/guidance
                * Case law citations (future)
                * Source URL and fetch date

        page: Page number for long statutes (1-10)
            Each page ~2000 words
            Only relevant for full Acts (mode="text")

    Returns:
        Legislation content in requested format:
        {
            "canonical_id": "/au-federal/fwa/2009/s394",
            "title": "Meaning of unfair dismissal",
            "content": "...",
            "mode": "summary",
            "cached": true,
            "fetch_date": "2025-12-23T10:30:00Z",
            "source_url": "https://www.legislation.gov.au/...",
            "cross_references": [
                {canonical_id: "/au-federal/fwa/2009/s385", title: "..."},
                ...
            ],
            "page": 1,
            "total_pages": 1
        }

    Side Effects:
        - If not cached: Downloads from official source
        - Updates local cache and metadata
        - Logs fetch operation

    Raises:
        ValueError: If canonical_id is invalid
        FileNotFoundError: If legislation not available
        IntegrityError: If cached content fails checksum
    """
```

#### Content Modes

**Mode: text**
```
Section 394 - Meaning of unfair dismissal

(1) A person has been unfairly dismissed if:
    (a) the person has been dismissed; and
    (b) the dismissal was harsh, unjust or unreasonable; and
    (c) the dismissal was not consistent with the Small Business
        Fair Dismissal Code; and
    (d) the dismissal was not a case of genuine redundancy.

Note: For the meaning of consistent with the Small Business Fair
Dismissal Code, see section 388.

[Cross-references: s.385 (What is a dismissal), s.396 (Genuine redundancy)]

Effective Date: 2009-07-01
Last Amended: 2021-03-27 (Fair Work Amendment Act 2021)
```

**Mode: summary**
```
## Unfair Dismissal - What It Means

You've been unfairly dismissed if your employer:
- Ended your employment (fired you, forced resignation, etc.)
- Did so in a way that was harsh, unjust, or unreasonable
- Didn't follow the Small Business Fair Dismissal Code (if applicable)
- Didn't have a genuine redundancy situation

### Key Points:
- "Harsh" = disproportionate to what you did wrong
- "Unjust" = you didn't actually do what you're accused of
- "Unreasonable" = unfair process, no warning, no chance to respond

### Who Can Claim:
- Employees (not independent contractors)
- Minimum employment period: 6 months (small business), 12 months (others)
- Earning below high income threshold (~$175,000)

### What This Means For You:
If you think you've been unfairly dismissed, you may be able to
lodge a claim with the Fair Work Commission within 21 days of
your dismissal.

[Related: s.385 (What counts as dismissal), s.396 (Genuine redundancy)]
```

**Mode: metadata**
```json
{
    "canonical_id": "/au-federal/fwa/2009/s394",
    "short_name": "FWA s.394",
    "full_name": "Fair Work Act 2009, Section 394",
    "title": "Meaning of unfair dismissal",
    "jurisdiction": "federal",
    "code_type": "primary_legislation",
    "enactment_date": "2009-06-25",
    "commencement_date": "2009-07-01",
    "current_version": "2021-03-27",
    "amendments": [
        {
            "date": "2021-03-27",
            "amending_act": "Fair Work Amendment Act 2021",
            "changes": "Updated high income threshold calculation"
        }
    ],
    "related_provisions": [
        {canonical_id: "/au-federal/fwa/2009/s385", relationship: "prerequisite"},
        {canonical_id: "/au-federal/fwa/2009/s396", relationship: "exception"}
    ],
    "related_regulations": [
        {canonical_id: "/au-federal/fwr/2009/reg3.01", title: "High income threshold"}
    ],
    "source_url": "https://www.legislation.gov.au/C2009A00028/latest/text",
    "cache_status": {
        "cached": true,
        "fetch_date": "2025-12-23T10:30:00Z",
        "checksum": "sha256:abc123...",
        "local_path": "data/legislation/cache/au-federal/fwa-2009.txt"
    }
}
```

### 2.3 Tool: get-support

**Purpose**: Provide actionable support pathways for workplace issues

#### Parameters

```python
def get_support(
    canonical_id: str | None = None,
    situation: str = "",
    jurisdiction: str = ""
) -> str:
    """Get support pathways and next steps.

    Args:
        canonical_id: Related legislation (optional but recommended)
            Example: "/au-federal/fwa/2009/s394"
            If provided, returns support specific to that legislation

        situation: Describe the workplace issue (optional)
            Examples:
            - "unfair dismissal"
            - "unpaid wages"
            - "workplace discrimination"
            - "unsafe working conditions"
            Used to filter relevant support pathways

        jurisdiction: Location for jurisdiction-specific support
            Examples:
            - "victoria"
            - "nsw"
            - "federal"
            Returns agencies operating in that jurisdiction

    Returns:
        Structured support pathway information:
        {
            "situation": "unfair dismissal",
            "jurisdiction": "victoria",
            "related_legislation": ["/au-federal/fwa/2009/s394"],
            "primary_agencies": [
                {
                    "name": "Fair Work Commission",
                    "role": "Handles unfair dismissal claims",
                    "contact": {
                        "phone": "1300 799 675",
                        "website": "https://www.fwc.gov.au",
                        "online_form": "https://www.fwc.gov.au/apply"
                    },
                    "cost": "free",
                    "eligibility": [
                        "Employed for minimum period (6-12 months)",
                        "Earning below high income threshold",
                        "Covered by Fair Work system"
                    ],
                    "timeframe": "Must apply within 21 days of dismissal"
                }
            ],
            "support_services": [
                {
                    "name": "Fair Work Ombudsman",
                    "role": "Free advice and information",
                    "contact": {...},
                    "cost": "free"
                },
                {
                    "name": "Community Legal Centre (Victoria)",
                    "role": "Free legal advice for eligible people",
                    "contact": {...},
                    "cost": "free (means-tested)"
                }
            ],
            "next_steps": [
                {
                    "step": 1,
                    "action": "Gather evidence",
                    "details": "Collect employment contract, termination letter, pay slips, any written communications",
                    "timeframe": "As soon as possible"
                },
                {
                    "step": 2,
                    "action": "Contact Fair Work Commission",
                    "details": "Call 1300 799 675 or lodge claim online within 21 days",
                    "timeframe": "Within 21 days of dismissal (strict deadline)"
                },
                {
                    "step": 3,
                    "action": "Seek legal advice (optional)",
                    "details": "Contact community legal centre for free advice if eligible",
                    "timeframe": "Before lodging claim (if possible)"
                }
            ],
            "important_deadlines": [
                {
                    "deadline": "21 days from dismissal",
                    "requirement": "Lodge unfair dismissal claim with FWC",
                    "consequence_if_missed": "Cannot pursue unfair dismissal remedy"
                }
            ],
            "estimated_timeline": "4-6 months from lodgement to hearing",
            "costs": "No filing fee. May want legal representation (costs vary)",
            "success_factors": [
                "Strong evidence of harsh/unjust/unreasonable dismissal",
                "Clear timeline of events",
                "Documented attempts to resolve with employer"
            ]
        }

    Raises:
        ValueError: If neither canonical_id nor situation provided
    """
```

#### Support Pathway Database Structure

```json
{
    "pathways": [
        {
            "pathway_id": "unfair-dismissal-federal",
            "situation": "unfair dismissal",
            "jurisdiction": "federal",
            "related_legislation": [
                "/au-federal/fwa/2009/s394",
                "/au-federal/fwa/2009/s385"
            ],
            "primary_agency": {
                "name": "Fair Work Commission",
                "jurisdiction": "federal",
                "contact": {...},
                "services": ["Unfair dismissal claims", "Conciliation", "Hearings"],
                "cost": "free",
                "eligibility_criteria": [...],
                "process_steps": [...]
            },
            "support_agencies": [...],
            "next_steps": [...],
            "deadlines": [...],
            "typical_timeline": "4-6 months",
            "success_rate": null,  // Future: add statistics if available
            "notes": "Federal system covers most private sector employees"
        }
    ]
}
```

## 3. Data Architecture

### 3.1 Canonical ID Format

```
/{jurisdiction}/{code-type}/{code}/{section?}/{subsection?}

Components:
- jurisdiction: au-federal | au-{state} | au-{territory}
- code-type: Primary identifier for legislation type
- code: Specific legislation code/year
- section: Section number (optional)
- subsection: Subsection reference (optional)

Examples:
/au-federal/fwa/2009/s394                    # Fair Work Act, Section 394
/au-federal/fwa/2009/s394/1                  # Subsection 1
/au-federal/fwa/2009/s394/1/a                # Paragraph (a)
/au-federal/fwr/2009/reg3.01                 # Fair Work Regulations
/au-victoria/ohs/2004/s21                    # OHS Act 2004 (VIC)
/au-victoria/eoa/2010                        # Equal Opportunity Act (full Act)
/au-nsw/ira/1996/s106                        # Industrial Relations Act (NSW)
```

### 3.2 Code Types

```
Primary Legislation (Acts):
- fwa = Fair Work Act
- ohs = Occupational Health and Safety Act
- eoa = Equal Opportunity Act
- lsl = Long Service Leave Act
- wca = Workers Compensation Act

Regulations:
- fwr = Fair Work Regulations
- ohsr = OHS Regulations
- eor = Equal Opportunity Regulations

Guidance (Non-Binding):
- fwc-guide = Fair Work Commission guidance
- fwo-fs = Fair Work Ombudsman fact sheets
```

### 3.3 Directory Structure

```
mcp-fair-shake/
├── data/
│   ├── legislation/
│   │   ├── cache/                           # Local cached legislation
│   │   │   ├── au-federal/
│   │   │   │   ├── fwa-2009.txt            # Full Act (raw text)
│   │   │   │   ├── fwa-2009-metadata.json  # Fetch metadata
│   │   │   │   ├── fwa-2009-sections.json  # Parsed sections
│   │   │   │   └── fwa-2009.checksum       # SHA256 hash
│   │   │   └── au-victoria/
│   │   │       ├── ohs-2004.txt
│   │   │       ├── ohs-2004-metadata.json
│   │   │       ├── ohs-2004-sections.json
│   │   │       └── ohs-2004.checksum
│   │   ├── summaries/                       # Plain language (Phase 2+)
│   │   │   ├── au-federal-fwa-2009-s394.md
│   │   │   └── au-victoria-ohs-2004-s21.md
│   │   └── parquet/                         # Optimized storage (Phase 2+)
│   │       ├── legislation.parquet
│   │       ├── sections.parquet
│   │       └── citations.parquet
│   ├── support-pathways/
│   │   ├── federal/
│   │   │   ├── fair-work-commission.json
│   │   │   ├── fair-work-ombudsman.json
│   │   │   └── pathways/
│   │   │       ├── unfair-dismissal.json
│   │   │       ├── wage-theft.json
│   │   │       └── discrimination.json
│   │   ├── victoria/
│   │   │   ├── worksafe-victoria.json
│   │   │   ├── veohrc.json
│   │   │   └── pathways/
│   │   │       ├── ohs-incident.json
│   │   │       └── discrimination.json
│   │   └── [other-states]/
│   └── metadata/
│       ├── cache-index.json                 # Inventory of cached content
│       ├── update-log.json                  # Last update check timestamps
│       └── sources.json                     # Official source URLs
├── src/
│   └── mcp_fair_shake/
│       ├── __init__.py                      # FastMCP server setup
│       ├── tools/
│       │   ├── resolve.py                   # resolve-legislation
│       │   ├── content.py                   # get-legislation-content
│       │   └── support.py                   # get-support
│       ├── data/
│       │   ├── cache.py                     # Cache management
│       │   ├── fetcher.py                   # Download from official sources
│       │   └── parser.py                    # Parse legislation structure
│       ├── ranking/
│       │   └── scorer.py                    # Result ranking logic
│       └── utils/
│           ├── canonical.py                 # ID parsing/validation
│           └── integrity.py                 # Checksum verification
└── tests/
    ├── test_resolve.py
    ├── test_content.py
    ├── test_support.py
    ├── test_cache.py
    └── fixtures/
        ├── sample-legislation.txt
        └── sample-metadata.json
```

### 3.4 Cache Metadata Format

```json
{
    "legislation_id": "au-federal-fwa-2009",
    "canonical_id": "/au-federal/fwa/2009",
    "source": {
        "url": "https://www.legislation.gov.au/C2009A00028/latest/text",
        "authority": "Federal Register of Legislation",
        "fetch_date": "2025-12-23T10:30:00Z",
        "fetch_method": "HTTP"
    },
    "integrity": {
        "checksum": "sha256:abc123...",
        "verified": true,
        "last_check": "2025-12-23T10:30:00Z"
    },
    "version": {
        "current": true,
        "as_at_date": "2025-12-23",
        "compilation_number": "C2024C00324",
        "last_amendment": {
            "date": "2021-03-27",
            "act": "Fair Work Amendment Act 2021"
        }
    },
    "structure": {
        "total_sections": 789,
        "parts": 6,
        "chapters": null,
        "schedules": 17
    },
    "files": {
        "raw_text": "data/legislation/cache/au-federal/fwa-2009.txt",
        "sections": "data/legislation/cache/au-federal/fwa-2009-sections.json",
        "checksum": "data/legislation/cache/au-federal/fwa-2009.checksum"
    },
    "size_bytes": 2458931,
    "update_schedule": "weekly"
}
```

## 4. Implementation Phases

### Phase 1: MVP (Weeks 1-2)
**Goal**: Basic legislation lookup for Victorian OHS Act

**Scope:**
- ✅ `resolve-legislation` (basic citation matching)
- ✅ `get-legislation-content` (text mode only)
- ✅ Single statute: Victorian OHS Act 2004
- ✅ Local text file caching
- ✅ Explicit "use fair-shake" trigger
- ✅ Test suite ≥80% coverage

**Deliverables:**
- Working MCP server
- OHS Act 2004 cached locally
- Basic search and retrieval
- Documentation

### Phase 2: Victorian Coverage (Weeks 3-4)
**Goal**: Comprehensive Victorian workplace legislation

**Scope:**
- ✅ All Victorian workplace Acts:
  - Equal Opportunity Act 2010
  - Long Service Leave Act 2018
  - Workers Compensation Act 1958
- ✅ Summary mode (plain language)
- ✅ Metadata mode
- ✅ Section filtering
- ✅ Parquet storage

**Deliverables:**
- 5+ Victorian Acts cached
- All three content modes working
- Parquet conversion pipeline
- Expanded test coverage

### Phase 3: Support Pathways (Weeks 5-6)
**Goal**: Map support agencies and next steps

**Scope:**
- ✅ `get-support` tool
- ✅ Victorian support agencies:
  - WorkSafe Victoria
  - VEOHRC (Victorian Equal Opportunity & Human Rights Commission)
  - Community legal centers
- ✅ Federal agencies:
  - Fair Work Commission
  - Fair Work Ombudsman
- ✅ Pathway templates for common scenarios

**Deliverables:**
- Support pathway database (JSON)
- 10+ common scenario pathways
- Contact information verified
- Deadline tracking

### Phase 4: Federal Coverage (Weeks 7-9)
**Goal**: Add federal workplace legislation

**Scope:**
- ✅ Fair Work Act 2009 (complete)
- ✅ Fair Work Regulations 2009
- ✅ Federal support pathways
- ✅ Jurisdiction filtering
- ✅ Modern Awards (sample - top 10 most common)

**Deliverables:**
- Federal legislation cached
- Jurisdiction-aware ranking
- Federal support agencies
- Award lookup (basic)

### Phase 5: National Coverage (Weeks 10-15)
**Goal**: All Australian states and territories

**Scope:**
- ✅ NSW, QLD, SA, WA, TAS, NT, ACT
- ✅ State-specific support agencies
- ✅ Automated update checks
- ✅ Data export capabilities

**Deliverables:**
- Comprehensive national coverage
- State-specific support pathways
- Weekly update automation
- Cache management tools

### Phase 6: Advanced (Future)
**Goal**: Enhanced capabilities

**Scope:**
- ✅ DuckDB integration
- ✅ Vector embeddings (semantic search)
- ✅ Natural language triggering (no "use fair-shake")
- ✅ Historical versions (as-in-force dates)
- ✅ Case law integration
- ✅ Conflict analysis

## 5. Technical Standards

### 5.1 Code Quality

- **Type Hints**: All functions fully typed (mypy strict mode)
- **Docstrings**: Google-style docstrings for all public functions
- **Test Coverage**: ≥80% line coverage, ≥90% for critical paths
- **Linting**: Ruff with project conventions
- **Formatting**: Ruff format

### 5.2 Error Handling

```python
# Good: Fail loudly with clear context
def resolve_legislation(query: str) -> str:
    if not query.strip():
        raise ValueError("Query cannot be empty")

    results = search_index(query)

    if not results:
        raise LookupError(
            f"No legislation found matching '{query}'. "
            f"Try: 'Fair Work Act', 'unfair dismissal', 'FWA s.394'"
        )

    return format_results(results)

# Bad: Silent failure
def resolve_legislation(query: str) -> str:
    results = search_index(query) or []
    return format_results(results)  # Returns empty without warning
```

### 5.3 Logging

```python
import logging

log = logging.getLogger(__name__)

def fetch_legislation(canonical_id: str) -> str:
    log.info(f"Fetching legislation: {canonical_id}")

    if is_cached(canonical_id):
        log.debug(f"Cache hit: {canonical_id}")
        return read_from_cache(canonical_id)

    log.warning(f"Cache miss: {canonical_id} - downloading from source")
    content = download_from_source(canonical_id)

    if not verify_checksum(content):
        log.error(f"Checksum verification failed: {canonical_id}")
        raise IntegrityError("Downloaded content failed integrity check")

    save_to_cache(canonical_id, content)
    log.info(f"Cached: {canonical_id}")

    return content
```

### 5.4 Data Integrity

```python
import hashlib

def verify_cached_content(canonical_id: str) -> bool:
    """Verify cached content hasn't been corrupted."""
    content = read_from_cache(canonical_id)
    stored_checksum = read_checksum(canonical_id)

    actual_checksum = hashlib.sha256(content.encode()).hexdigest()

    if actual_checksum != stored_checksum:
        log.error(f"Integrity check failed: {canonical_id}")
        log.error(f"Expected: {stored_checksum}")
        log.error(f"Actual: {actual_checksum}")
        return False

    return True
```

## 6. Security & Privacy

### 6.1 Data Sources

- **Only official government sources**: legislation.gov.au, state parliamentary websites
- **No third-party APIs**: Avoid dependencies on commercial services
- **Source verification**: Checksums and HTTPS validation

### 6.2 User Data

- **No user data collection**: MCP server is stateless
- **No analytics**: No tracking or usage statistics
- **No external requests**: All data served from local cache after initial fetch

### 6.3 Disclaimers

All responses must include:

```
⚖️ DISCLAIMER: This is general legal information, not legal advice.
For advice specific to your situation, consult a lawyer or contact
[relevant support agency].
```

## 7. Performance Targets

### 7.1 Latency

- **Cache hit** (legislation content): < 100ms
- **Cache miss** (first fetch): < 5 seconds
- **Resolution** (search): < 500ms
- **Support lookup**: < 200ms

### 7.2 Throughput

- **Concurrent requests**: 10+ simultaneous
- **Daily queries**: 10,000+ (with caching)

### 7.3 Storage

- **Per statute**: ~500KB - 5MB (raw text)
- **Total Phase 1**: ~5MB (single Act)
- **Total Phase 5**: ~500MB (all jurisdictions)
- **Parquet compression**: ~60% reduction

## 8. Testing Strategy

### 8.1 Unit Tests

- Each tool tested independently
- Mock external data sources
- Test error conditions explicitly
- Parametrized tests for multiple scenarios

### 8.2 Integration Tests

- End-to-end query workflows
- Cache read/write operations
- Checksum verification
- Data integrity checks

### 8.3 Fixtures

```python
# Sample legislation for testing
SAMPLE_LEGISLATION = {
    "canonical_id": "/au-federal/fwa/2009/s394",
    "text": "Section 394 - Meaning of unfair dismissal...",
    "metadata": {...},
    "checksum": "sha256:abc123..."
}

# Sample queries for ranking tests
QUERY_TESTS = [
    ("unfair dismissal", "/au-federal/fwa/2009/s394"),
    ("FWA s.394", "/au-federal/fwa/2009/s394"),
    ("casual employee rights", "/au-federal/fwa/2009/s86"),
]
```

## 9. Documentation Requirements

### 9.1 User Documentation

- ✅ README.md with quick start
- ✅ TESTING.md with test instructions
- ✅ Tool descriptions in MCP schema
- ✅ Example queries and responses

### 9.2 Developer Documentation

- ✅ REQUIREMENTS.md (this document's source)
- ✅ SPECIFICATION.md (this document)
- ✅ Architecture diagrams
- ✅ Data flow diagrams
- ✅ Phased roadmap

### 9.3 Code Documentation

- ✅ Docstrings for all public functions
- ✅ Inline comments for complex logic
- ✅ Type hints for all parameters
- ✅ README in each major module

## 10. Success Metrics

### Phase 1 Success:
- [ ] 100% of test queries return correct OHS Act sections
- [ ] All 3 tools working with test coverage ≥80%
- [ ] Cache latency < 100ms
- [ ] Zero silent failures

### Phase 3 Success:
- [ ] Users find relevant support in ≤2 queries
- [ ] Support pathways cover 90% of common scenarios
- [ ] Contact information verified and current
- [ ] Deadline tracking accurate

### Phase 5 Success:
- [ ] National coverage (all states/territories)
- [ ] Update automation running weekly
- [ ] Data export functional
- [ ] Offline operation supported

## References

- [Context7 MCP Analysis](./context7-analysis.md)
- [arXiv MCP Analysis](./arxiv-mcp-analysis.md)
- [MCP Fair Shake Requirements](./REQUIREMENTS.md)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Federal Register of Legislation](https://www.legislation.gov.au/)
- [Victorian Legislation](https://www.legislation.vic.gov.au/)
