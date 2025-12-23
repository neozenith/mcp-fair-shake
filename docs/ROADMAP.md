# MCP Fair Shake - Implementation Roadmap

**Version:** 1.0
**Last Updated:** 2025-12-23
**Current Phase:** Planning → Phase 1

## Quick Reference

| Phase | Focus | Duration | Status |
|-------|-------|----------|--------|
| **Phase 1** | MVP - Victorian OHS Act | Weeks 1-2 | 🔵 Planning |
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
- [ ] FastMCP server with tool registration
- [ ] `resolve_legislation()` function (basic)
- [ ] `get_legislation_content()` function (text mode)
- [ ] Cache management module
- [ ] Legislation fetcher (HTTP download)
- [ ] Canonical ID parser/validator
- [ ] Checksum verification

**Data:**
- [ ] OHS Act 2004 cached locally
- [ ] Metadata tracked (source URL, fetch date, checksum)
- [ ] Section index created

**Tests:**
- [ ] Test suite ≥80% coverage
- [ ] Tool integration tests
- [ ] Cache read/write tests
- [ ] Checksum verification tests
- [ ] Error handling tests

**Documentation:**
- [ ] README updated with Phase 1 usage
- [ ] Tool descriptions in MCP schema
- [ ] Example queries documented

### Tasks

#### Week 1: Core Infrastructure

**Day 1-2: Project Setup**
- [x] Remove placeholder `evaluate` tool
- [ ] Create `data/` directory structure
- [ ] Implement canonical ID parser
  - Parse `/au-victoria/ohs/2004/s21`
  - Validate ID format
  - Extract jurisdiction, code, section
- [ ] Implement cache module
  - Read/write text files
  - Load/save metadata
  - Check cache existence

**Day 3-4: Legislation Fetcher**
- [ ] Research legislation.vic.gov.au API/scraping
- [ ] Implement HTTP fetcher
  - Download OHS Act 2004
  - Handle errors (network, 404, etc.)
  - Retry logic
- [ ] Implement checksum generation (SHA256)
- [ ] Implement metadata tracking
  - Source URL
  - Fetch timestamp
  - Content hash

**Day 5: Parsing & Indexing**
- [ ] Parse legislation structure
  - Extract sections
  - Build section index
  - Identify cross-references
- [ ] Store parsed sections as JSON
- [ ] Test with OHS Act 2004

#### Week 2: Tools & Testing

**Day 6-7: resolve-legislation Tool**
- [ ] Implement basic citation matching
  - Exact citation: "OHS Act s.21"
  - Section number: "section 21"
  - Full name: "Occupational Health and Safety Act 2004"
- [ ] Return canonical ID
- [ ] Handle "not found" cases
- [ ] Write unit tests

**Day 8-9: get-legislation-content Tool**
- [ ] Implement content retrieval
  - Check cache first
  - Auto-download if missing
  - Return text content
- [ ] Implement section filtering
  - Full Act vs. specific section
  - Handle subsections
- [ ] Implement pagination (basic)
- [ ] Write integration tests

**Day 10: Quality & Polish**
- [ ] Run full test suite (aim for 80%+)
- [ ] Fix any failing tests
- [ ] Test with `make claude` (one-off testing)
- [ ] Update documentation
- [ ] Code review and refactor

### Success Criteria

- [x] All 3 tools functional (2/3 - support deferred to Phase 3)
- [ ] OHS Act 2004 cached and queryable
- [ ] Test coverage ≥ 80%
- [ ] Zero silent failures
- [ ] Cache latency < 100ms
- [ ] Documentation complete

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

- [ ] 5+ Victorian Acts cached
- [ ] All 3 modes working (text, summary, metadata)
- [ ] Parquet storage functional
- [ ] Query performance < 500ms

---

## Phase 3: Support Pathways (Weeks 5-6)

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

## Phase 4: Federal Coverage (Weeks 7-9)

**Goal**: Add federal workplace legislation

### Scope

**Legislation:**
- Fair Work Act 2009 (complete)
- Fair Work Regulations 2009
- Sample Modern Awards (top 10 most common)

**Features:**
- Jurisdiction filtering (federal vs. state)
- Conflict resolution (federal overrides state)
- Award lookup (basic)

### Tasks

**Week 7: Fair Work Act**
- [ ] Fetch Fair Work Act 2009
  - Source: legislation.gov.au
  - All sections, schedules
- [ ] Cache and parse
- [ ] Update resolution ranking
  - Prioritize federal for federal queries
  - Consider jurisdiction hierarchy

**Week 8: Regulations & Awards**
- [ ] Fetch Fair Work Regulations 2009
- [ ] Research Modern Awards API/access
- [ ] Fetch sample awards
  - Clerks Award
  - Restaurant Award
  - General Retail Award
  - etc.
- [ ] Implement award lookup (basic)

**Week 9: Federal Support**
- [ ] Add FWC processes
- [ ] Add FWO complaint pathways
- [ ] Test federal + state coverage
- [ ] Integration testing

### Success Criteria

- [ ] Fair Work Act fully cached
- [ ] Regulations accessible
- [ ] Sample awards available
- [ ] Federal/state filtering works
- [ ] Support pathways include FWC/FWO

---

## Phase 5: National Coverage (Weeks 10-15)

**Goal**: All Australian states and territories

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
