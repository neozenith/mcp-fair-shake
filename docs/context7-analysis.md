# Context7 MCP Architecture Analysis

This document analyzes the Context7 MCP design to inform the legislation lookup MCP implementation.

## Overview

Context7 is an MCP server that provides up-to-date technical documentation lookup for libraries and frameworks. It follows a **two-step resolution pattern** that separates name resolution from content retrieval.

## Core Architecture Pattern

### 1. Two-Step Tool Pattern

**Tool 1: resolve-library-id**
- **Purpose**: Converts a human-friendly library name into a canonical library ID
- **Input**: `libraryName` (string) - e.g., "next.js", "react", "mongodb"
- **Output**: List of matching libraries with Context7-compatible IDs
- **Selection Logic**:
  - Name similarity to query (exact matches prioritized)
  - Description relevance to query intent
  - Documentation coverage (prioritize higher code snippet counts)
  - Source reputation (High/Medium sources more authoritative)
  - Benchmark Score (quality indicator, 100 = highest)

**Tool 2: get-library-docs**
- **Purpose**: Fetches actual documentation content using the resolved library ID
- **Input**:
  - `context7CompatibleLibraryID` (required) - Format: `/org/project` or `/org/project/version`
  - `topic` (optional) - Focuses on specific subjects (e.g., "routing", "hooks")
  - `page` (optional, 1-10, default 1) - Pagination for large result sets
  - `mode` (optional, "code"|"info", default "code")
- **Output**: Documentation content focused on the requested topic

### 2. Mode-Based Content Retrieval

Context7 uses a **mode parameter** to differentiate content types:

- **`mode="code"`** (default): API references, code examples, technical specs
- **`mode="info"`**: Conceptual guides, narrative documentation, architectural information

This allows the same tool to serve different use cases without tool proliferation.

### 3. Triggering Mechanisms

Context7 uses **explicit user invocation**:
- User includes phrases like "use context7" in prompts
- Can be configured for automatic invocation through editor rules
- No automatic "smart detection" - requires explicit trigger

### 4. Workflow Pattern

```
User Query
    ↓
Detect library reference (e.g., "Next.js routing")
    ↓
resolve-library-id("Next.js")
    ↓
Returns: /vercel/next.js (+ alternatives if ambiguous)
    ↓
get-library-docs(
    context7CompatibleLibraryID="/vercel/next.js",
    topic="routing",
    mode="code"
)
    ↓
Documentation injected into LLM context
    ↓
LLM responds with current, accurate information
```

### 5. Key Design Principles

1. **Separation of Concerns**: Resolution separate from retrieval
2. **Explicit over Implicit**: User-triggered, not auto-detected
3. **Focused Retrieval**: Topic-based filtering reduces noise
4. **Pagination Support**: Handles large documentation sets
5. **Mode Flexibility**: Single tool serves multiple content types
6. **Canonical IDs**: Stable identifiers for versioned content

### 6. Error Handling Pattern

From the tool descriptions:
- Clear error messages for missing/invalid library IDs
- Suggestions for query refinement when no matches
- Acknowledgment of multiple good matches with explanation of choice
- Request for clarification on ambiguous queries

## Application to Legislation Lookup

### Proposed Tool Structure

**Tool 1: resolve-legislation**
```
Input: legislationQuery (string)
- e.g., "clean water act", "ADA title III", "GDPR article 17"

Selection Logic:
- Name/citation similarity (exact citations prioritized)
- Jurisdiction match (federal/state/international)
- Enactment date vs. current version
- Authority level (constitutional > statutory > regulatory)
- Amendment status (current vs. historical)

Output: List of matching legislation with canonical IDs
- Format: `/{jurisdiction}/{act-code}/{section}` or `/{country}/{regulation}/{article}`
```

**Tool 2: get-legislation-content**
```
Input:
- canonicalLegislationID (required)
- section (optional) - Focus on specific sections/articles
- page (optional, 1-10) - For long statutes
- mode (optional, "text"|"summary"|"metadata")
  - "text": Full statutory text, citations, cross-references
  - "summary": Plain language summaries, key provisions
  - "metadata": Enactment date, amendments, related cases

Output: Legislation content focused on request
```

### Triggering Strategy

**Option 1: Explicit Trigger** (Context7 style)
- Require "use fair-shake" or similar phrase
- Pros: Predictable, user-controlled
- Cons: Extra typing, must remember trigger phrase

**Option 2: Smart Detection**
- Detect legislation references in queries automatically
- Patterns: USC citations, CFR references, Act names
- Pros: Seamless UX, no trigger needed
- Cons: False positives, more complex

**Recommendation**: Start with explicit trigger, add smart detection later

### Workflow Example

```
User: "use fair-shake: What are the requirements for ADA Title III compliance?"
    ↓
Detect legislation reference: "ADA Title III"
    ↓
resolve-legislation("ADA Title III")
    ↓
Returns: /us-federal/ada/title-iii
    ↓
get-legislation-content(
    canonicalLegislationID="/us-federal/ada/title-iii",
    section="public accommodations",
    mode="summary"
)
    ↓
Plain language summary injected into context
    ↓
LLM explains requirements in accessible terms
```

### Additional Considerations for Legislation

1. **Versioning**: Legislation changes over time
   - Track amendment dates
   - Support historical vs. current text
   - Handle effective dates

2. **Jurisdiction Hierarchy**:
   - Federal > State > Local
   - International treaties and agreements
   - Conflict of laws handling

3. **Cross-References**:
   - Related regulations (CFR for USC)
   - Case law interpretations
   - Administrative guidance

4. **Authority Levels**:
   - Constitutional provisions
   - Statutes (USC, state codes)
   - Regulations (CFR, state regs)
   - Administrative interpretations

## Implementation Recommendations

### Phase 1: MVP (Mirror Context7)
1. Implement two-tool pattern (resolve + get-content)
2. Support basic text mode only
3. Explicit trigger phrase required
4. Simple citation matching (exact matches)
5. Single jurisdiction (e.g., US Federal only)

### Phase 2: Enhanced Functionality
1. Add summary and metadata modes
2. Implement smart detection for common citations
3. Add state/local jurisdiction support
4. Include cross-reference lookup
5. Track amendments and versioning

### Phase 3: Advanced Features
1. Case law integration
2. Regulatory guidance lookup
3. International law support
4. Natural language query understanding
5. Conflict analysis tools

## Technical Architecture

### Canonical ID Format

```
/{jurisdiction}/{code-type}/{code}/{section?}/{subsection?}

Examples:
/us-federal/usc/42/12101              # ADA, 42 USC § 12101
/us-federal/cfr/29/1630               # EEOC regulations
/california/codes/civ/51              # Unruh Civil Rights Act
/eu/gdpr/article/17                   # GDPR Right to Erasure
```

### Database Schema Considerations

```
Legislation:
- canonical_id (primary key)
- jurisdiction
- code_type (usc, cfr, state_code, etc.)
- short_name (e.g., "ADA")
- full_name
- enactment_date
- effective_date
- current_version
- amendments (array)

Sections:
- section_id (primary key)
- legislation_id (foreign key)
- section_number
- title
- text
- effective_date
- amended_by (array)

Citations:
- citation_id (primary key)
- section_id (foreign key)
- citation_format (e.g., "42 USC § 12101")
- citation_type (official, popular)
```

## Sources

- [Context7 GitHub Repository](https://github.com/upstash/context7)
- [Context7 MCP Blog Post](https://upstash.com/blog/context7-mcp)
- [Context7 on Smithery](https://smithery.ai/server/@upstash/context7-mcp)
- [MCP Tool Definitions](mcp://context7/tools)
