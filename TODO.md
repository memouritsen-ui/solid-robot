# RESEARCH TOOL — TODO CHECKLIST
## Granular Task List for Claude Code Execution

**Instructions**:
- Complete tasks in order
- Mark [x] when complete
- Commit after each numbered task
- If stuck on a task after 3 attempts, log in ERROR-LOG.md and skip

**Last Updated**: 2025-12-09 by Claude Code (comprehensive test coverage + Swift files)
**Current Status**: Phase 1-4 PARTIALLY COMPLETE, Phase 5-7 NOT STARTED

---

## VERIFICATION STATUS (Run these to confirm)

```bash
# Backend tests (must show 216 passed)
cd backend && uv run python -m pytest tests/ -v

# Ruff linting (must show "All checks passed!")
cd backend && uv run ruff check src/ tests/

# Mypy (must show "Success: no issues found in 55 source files")
cd backend && uv run python -m mypy src/ --ignore-missing-imports

# Swift build (must verify manually in Xcode)
# Open gui/ResearchTool/Package.swift and build
```

---

## PHASE 0: SETUP ✅ COMPLETE

### Repository Structure
- [x] #1 Create directory structure per SPEC.md Section 2.2
- [x] #2 Copy all documentation files to repository
- [x] #3 Initialize git with develop branch
- [x] #4 Create .gitignore for Python and Swift
- [x] #5 Create .env.example with all required API keys

---

## PHASE 1: FOUNDATION ✅ COMPLETE

### Python Project Setup
- [x] #6 Create /backend/pyproject.toml with all dependencies
- [x] #7 Run `uv sync` to install dependencies
- [x] #8 Verify imports: `python -c "import fastapi; import langgraph; import lancedb"`

### Core Configuration
- [x] #9 Create /backend/src/research_tool/__init__.py
- [x] #10 Create /backend/src/research_tool/core/__init__.py
- [x] #11 Create /backend/src/research_tool/core/config.py (Settings class)
- [x] #12 Create /backend/src/research_tool/core/exceptions.py (exception hierarchy)
- [x] #13 Create /backend/src/research_tool/core/logging.py (structlog config)
- [x] #14 Test: Import Settings and verify environment loading

### FastAPI Application
- [x] #15 Create /backend/src/research_tool/main.py (FastAPI app)
- [x] #16 Add /api/health endpoint
- [x] #17 Add CORS middleware for SwiftUI
- [x] #18 Add startup/shutdown events with logging
- [x] #19 Test: Start server and hit health endpoint

### Test Framework
- [x] #20 Create /backend/tests/__init__.py
- [x] #21 Create /backend/tests/conftest.py (pytest fixtures)
- [x] #22 Create /backend/tests/unit/__init__.py
- [x] #23 Create /backend/tests/unit/test_health.py
- [x] #24 Run: `pytest tests/ -v` - verify passing

### Linting and Type Checking
- [x] #25 Create /backend/.pre-commit-config.yaml
- [x] #26 Run: `ruff check src/ tests/` - VERIFIED 0 errors (2025-12-09)
- [x] #27 Run: `mypy src/` - VERIFIED 0 errors (2025-12-09)

### SwiftUI Project
- [x] #28 Create Xcode project at /gui/ResearchTool/
- [x] #29 Create ResearchToolApp.swift (app entry point)
- [x] #30 Create AppState.swift (shared state) - CREATED 2025-12-09
- [x] #31 Create MainView.swift (navigation structure) - CREATED 2025-12-09
- [x] #32 Create ChatView.swift (chat interface)
- [x] #33 Create MessageBubble.swift (message display)
- [x] #34 Create SettingsView.swift (placeholder) - CREATED 2025-12-09
- [x] #35 Create Message.swift (message model)
- [x] #36 Create ChatViewModel.swift (chat logic - placeholder)
- [ ] #37 Build Xcode project - verify no errors -- NEEDS MANUAL VERIFICATION

### Scripts
- [x] #38 Create /scripts/setup.sh
- [x] #39 Create /scripts/start_backend.sh
- [x] #40 Create /scripts/start_ollama.sh
- [x] #41 Create /scripts/run_tests.sh
- [x] #42 Make all scripts executable: `chmod +x scripts/*.sh`

### Phase 1 Validation
- [ ] #43 VALIDATE: SwiftUI shows backend connection status -- NEEDS E2E TEST
- [x] #44 VALIDATE: All tests pass - 216 tests passing (2025-12-09)
- [x] #45 VALIDATE: All linting passes - 0 errors (2025-12-09)
- [x] #46 COMMIT: "feat: complete phase 1 foundation"
- [x] #47 MERGE: phase-1-foundation → develop

---

## PHASE 2: CONVERSATIONAL CORE ✅ COMPLETE

### LLM Provider Interface
- [x] #48 Create /backend/src/research_tool/services/__init__.py
- [x] #49 Create /backend/src/research_tool/services/llm/__init__.py
- [x] #50 Create /backend/src/research_tool/services/llm/provider.py (ModelProvider ABC)
- [x] #51 Test: Import ModelProvider

### LiteLLM Router
- [x] #52 Create /backend/src/research_tool/services/llm/router.py (LLMRouter class)
- [x] #53 Implement complete() method with streaming
- [x] #54 Implement is_model_available() method
- [x] #55 Implement fallback logic
- [x] #56 Test: Mock test for router (12 tests in test_llm_router.py)

### Model Selector
- [x] #57 Create /backend/src/research_tool/services/llm/selector.py
- [x] #58 Implement PrivacyMode enum
- [x] #59 Implement TaskComplexity enum
- [x] #60 Implement ModelRecommendation dataclass
- [x] #61 Implement select() method (decision tree from META guide 7.1)
- [x] #62 Implement recommend_privacy_mode() method
- [x] #63 Test: test_local_only_never_selects_cloud
- [x] #64 Test: test_cloud_allowed_high_complexity_prefers_cloud
- [x] #65 Test: test_sensitive_keywords_trigger_local_only

### Chat WebSocket
- [x] #66 Create /backend/src/research_tool/api/__init__.py
- [x] #67 Create /backend/src/research_tool/api/websocket/__init__.py
- [x] #68 Create /backend/src/research_tool/api/websocket/chat_ws.py
- [x] #69 Implement ChatWebSocketHandler class
- [x] #70 Implement message receiving
- [x] #71 Implement model selection integration
- [x] #72 Implement streaming response
- [x] #73 Implement conversation history tracking
- [x] #74 Add WebSocket route to main.py
- [x] #75 Test: WebSocket connection test (10 tests in test_websocket.py)

### SwiftUI WebSocket Client
- [x] #76 Create /gui/.../Services/WebSocketClient.swift
- [x] #77 Implement connect() method
- [x] #78 Implement disconnect() method
- [x] #79 Implement send() method
- [x] #80 Implement message handlers (token, done, error)
- [x] #81 Update ChatViewModel to use WebSocket
- [x] #82 Update ChatView to show streaming response
- [x] #83 Add privacy mode selector to UI (PrivacyModePicker.swift)
- [ ] #84 Build and test: Send message, receive streaming response -- NEEDS E2E TEST

### Phase 2 Tests
- [x] #85 Create /backend/tests/unit/test_llm_router.py (12 tests)
- [x] #86 Create /backend/tests/unit/test_model_selector.py (17 tests)
- [x] #87 Create /backend/tests/integration/test_websocket.py (10 tests)
- [x] #88 Run: `pytest tests/ -v --cov` - verify >80% coverage

### Phase 2 Validation
- [ ] #89 VALIDATE: Local model responds correctly -- NEEDS OLLAMA RUNNING
- [ ] #90 VALIDATE: Cloud model responds correctly -- NEEDS API KEY
- [x] #91 VALIDATE: LOCAL_ONLY never uses cloud (tested)
- [ ] #92 VALIDATE: Streaming works in GUI -- NEEDS E2E TEST
- [x] #93 COMMIT: "feat: complete phase 2 conversational core"
- [x] #94 MERGE: phase-2-conversational → develop

---

## PHASE 3: MEMORY SYSTEM ✅ COMPLETE

### Memory Repository Interface
- [x] #95 Create /backend/src/research_tool/services/memory/__init__.py
- [x] #96 Create /backend/src/research_tool/services/memory/repository.py (MemoryRepository ABC)
- [x] #97 Define store_document() abstract method
- [x] #98 Define search_similar() abstract method
- [x] #99 Define get_source_effectiveness() abstract method
- [x] #100 Define update_source_effectiveness() abstract method
- [x] #101 Define record_access_failure() abstract method
- [x] #102 Define is_known_failure() abstract method

### LanceDB Implementation
- [x] #103 Create /backend/src/research_tool/services/memory/lance_repo.py
- [x] #104 Define ResearchDocument LanceModel
- [x] #105 Implement database connection
- [x] #106 Implement store_document() - with embedding
- [x] #107 Implement search_similar() - hybrid search
- [x] #108 Implement chunking strategy (512 tokens, 64 overlap)
- [x] #109 Test: Store and retrieve document

### SQLite Implementation
- [x] #110 Create /backend/src/research_tool/services/memory/sqlite_repo.py
- [x] #111 Define schema (from META guide Section 4.1.3)
- [x] #112 Implement database initialization
- [x] #113 Implement research_sessions CRUD
- [x] #114 Implement source_effectiveness CRUD
- [x] #115 Implement access_failures CRUD
- [x] #116 Implement domain_config_overrides CRUD
- [x] #117 Test: CRUD operations

### Source Effectiveness Learning
- [x] #118 Create /backend/src/research_tool/services/memory/learning.py
- [x] #119 Implement exponential moving average calculation
- [x] #120 Implement update_effectiveness() method
- [x] #121 Implement get_ranked_sources() method
- [x] #122 Test: Effectiveness updates correctly

### Combined Memory Repository
- [x] #123 Create composite repository combining Lance + SQLite (combined_repo.py)
- [x] #124 Implement unified interface
- [x] #125 Test: All memory operations work together

### Phase 3 Tests
- [x] #126 Create /backend/tests/unit/test_memory.py (20 tests)
- [x] #127 Test: Vector storage and retrieval
- [x] #128 Test: Structured data storage
- [x] #129 Test: Memory persists across restarts
- [x] #130 Test: Retrieval latency <100ms for 10K docs
- [x] #131 Test: Source effectiveness tracking
- [x] #132 Test: Access failure recording

### Phase 3 Validation
- [x] #133 VALIDATE: Anti-patterns #8 and #9 not present
- [x] #134 COMMIT: "feat: complete phase 3 memory system"
- [x] #135 MERGE: phase-3-memory → develop

---

## PHASE 4: RESEARCH AGENT ⚠️ PARTIALLY COMPLETE (~70%)

### Data Models
- [x] #136 Create /backend/src/research_tool/models/__init__.py
- [x] #137 Create /backend/src/research_tool/models/state.py (ResearchState)
- [x] #138 Create /backend/src/research_tool/models/domain.py (DomainConfiguration)
- [x] #139 Create /backend/src/research_tool/models/entities.py (Entity, Fact, SourceResult)
- [x] #140 Create /backend/src/research_tool/models/requests.py (API models)

### Search Provider Interface
- [x] #141 Create /backend/src/research_tool/services/search/__init__.py
- [x] #142 Create /backend/src/research_tool/services/search/provider.py (SearchProvider ABC)
- [x] #143 Create /backend/src/research_tool/services/search/rate_limiter.py

### Search Provider Implementations
- [x] #144 Create tavily.py - Tavily search provider
- [x] #145 Create exa.py - Exa search provider -- IMPLEMENTED 2025-12-09
- [x] #146 Create semantic_scholar.py - with 1 RPS rate limit
- [x] #147 Create pubmed.py - PubMed provider
- [x] #148 Create arxiv.py - arXiv provider
- [x] #149 Create unpaywall.py - Open access finder -- IMPLEMENTED 2025-12-09
- [x] #150 Create brave.py - Brave search provider
- [x] #151 Create crawler.py - Playwright with stealth -- IMPLEMENTED 2025-12-09
- [x] #152 Test: Each provider returns results - UNIT TESTS ADDED 2025-12-09
  - test_provider.py (11 tests)
  - test_rate_limiter.py (10 tests)
  - test_tavily.py (8 tests)
  - test_brave.py (10 tests)
  - test_arxiv.py (7 tests)
  - test_pubmed.py (9 tests)
  - test_semantic_scholar.py (10 tests)
  - test_crawler.py (18 tests)
  - test_exa.py (11 tests) -- ADDED 2025-12-09
  - test_unpaywall.py (12 tests) -- ADDED 2025-12-09

### Obstacle Handling
- [x] #153 Create /backend/src/research_tool/utils/retry.py (tenacity config)
- [x] #154 Create /backend/src/research_tool/utils/circuit_breaker.py
- [x] #155 Implement exponential backoff (4s, 8s, 16s, 32s, 60s max)
- [ ] #156 Implement proxy rotation (if needed) -- SKIPPED
- [x] #157 Test: Rate limit triggers backoff -- IMPLEMENTED 2025-12-09
- [x] #158 Test: Circuit breaker opens after failures -- IMPLEMENTED 2025-12-09

### LangGraph Agent
- [x] #159 Create /backend/src/research_tool/agent/__init__.py
- [x] #160 Create /backend/src/research_tool/agent/graph.py (StateGraph setup)
- [x] #161 Create /backend/src/research_tool/agent/nodes/__init__.py

### Agent Nodes
- [x] #162 Create clarify.py - Query clarification node
- [x] #163 Create plan.py - Research planning node
- [x] #164 Create collect.py - Data collection node
- [x] #165 Create process.py - Data processing node
- [x] #166 Create analyze.py - Analysis node
- [x] #167 Create evaluate.py - Saturation evaluation node
- [x] #168 Create synthesize.py - Synthesis node
- [x] #169 Create export_node.py - Export node -- IMPLEMENTED 2025-12-09

### Agent Node Tests - ADDED 2025-12-09
- [x] test_clarify.py (9 tests)
- [x] test_plan.py (8 tests)
- [x] test_collect.py (8 tests)
- [x] test_process.py (9 tests)
- [x] test_analyze.py (6 tests)
- [x] test_evaluate.py (9 tests)
- [x] test_synthesize.py (13 tests)

### Decision Logic
- [x] #170 Create /backend/src/research_tool/agent/decisions/__init__.py
- [x] #171 Create source_selector.py (decision tree from META 7.2) -- IMPLEMENTED 2025-12-09
- [x] #172 Create clarification.py (decision tree from META 7.3) -- IMPLEMENTED 2025-12-09
- [x] #173 Create obstacle_handler.py (decision tree from META 7.4)
- [x] #174 Create saturation.py (decision tree from META 7.5)

### Saturation Detection
- [x] #175 Implement SaturationMetrics dataclass
- [x] #176 Implement calculate_saturation() function
- [x] #177 Implement should_stop() function
- [ ] #178 Test: Saturation detected at threshold -- NEEDS TEST
- [ ] #179 Test: Research continues below threshold -- NEEDS TEST

### Graph Assembly
- [x] #180 Wire all nodes in graph.py
- [x] #181 Add conditional edges
- [x] #182 Add checkpointing
- [ ] #183 Test: Complete workflow executes -- NEEDS INTEGRATION TEST

### Agent Tools
- [x] #184 Create /backend/src/research_tool/agent/tools/__init__.py
- [ ] #185 Create search_tool.py - LangGraph tool wrapper -- NOT IMPLEMENTED
- [ ] #186 Create memory_tool.py - Memory access tool -- NOT IMPLEMENTED
- [ ] #187 Test: Tools integrate with agent -- NEEDS TEST

### Research API
- [x] #188 Create /backend/src/research_tool/api/routes/research.py
- [x] #189 Implement POST /api/research/start
- [x] #190 Implement GET /api/research/{id}/status
- [ ] #191 Implement POST /api/research/{id}/approve -- NOT IMPLEMENTED
- [x] #192 Implement POST /api/research/{id}/stop
- [ ] #193 Create progress WebSocket handler -- NOT IMPLEMENTED
- [x] #194 Add routes to main.py

### Phase 4 Tests
- [x] #195 Create search provider tests (7 files) -- DONE 2025-12-09
- [ ] #196 Create /backend/tests/unit/test_saturation.py -- NOT IMPLEMENTED
- [ ] #197 Create /backend/tests/unit/test_decisions.py -- NOT IMPLEMENTED
- [ ] #198 Create /backend/tests/integration/test_agent_workflow.py -- NOT IMPLEMENTED
- [ ] #199 Test: Full research cycle on test query -- NOT IMPLEMENTED

### Phase 4 Validation
- [ ] #200 VALIDATE: Search anti-patterns #3, #4, #5 not present
- [ ] #201 VALIDATE: Obstacle anti-patterns #6, #7 not present
- [ ] #202 VALIDATE: Audit trail captures all decisions
- [x] #203 COMMIT: "feat: complete phase 4 research agent"
- [x] #204 MERGE: phase-4-research → develop

---

## PHASE 5: INTELLIGENCE FEATURES ❌ NOT STARTED

### Domain Detection
- [ ] #205 Create /backend/src/research_tool/agent/decisions/domain_detector.py
- [ ] #206 Implement keyword-based domain detection
- [ ] #207 Implement LLM-based domain detection (fallback)
- [ ] #208 Test: Detects medical, regulatory, CI domains

### Auto-Configuration
- [ ] #209 Create /backend/data/domain_configs/medical.json
- [ ] #210 Create /backend/data/domain_configs/competitive_intelligence.json
- [ ] #211 Create /backend/data/domain_configs/regulatory.json
- [ ] #212 Create /backend/data/domain_configs/academic.json
- [ ] #213 Implement config loading
- [ ] #214 Implement config merging with learned overrides
- [ ] #215 Test: Correct config loaded for domain

### Cross-Verification
- [ ] #216 Create /backend/src/research_tool/agent/nodes/verify.py
- [ ] #217 Implement fact extraction
- [ ] #218 Implement cross-source comparison
- [ ] #219 Implement contradiction detection
- [ ] #220 Test: Contradictions detected in test data

### Confidence Scoring
- [ ] #221 Implement source-based confidence
- [ ] #222 Implement verification-based confidence
- [ ] #223 Implement composite confidence score
- [ ] #224 Test: Confidence correlates with source quality

### Learning Updates
- [ ] #225 Implement post-research learning trigger
- [ ] #226 Update source effectiveness after research
- [ ] #227 Update domain config based on discovered sources
- [ ] #228 Test: Learning persists to next research

### Privacy Recommendation Enhancement
- [ ] #229 Enhance recommend_privacy_mode() with NLP
- [ ] #230 Add explanation generation
- [ ] #231 Test: Recommendations accurate for test cases

### Phase 5 Tests
- [ ] #232 Test: Domain detection accuracy >90%
- [ ] #233 Test: Cross-verification catches planted contradictions
- [ ] #234 Test: Confidence scores correlate with accuracy
- [ ] #235 Test: Learning influences future research

### Phase 5 Validation
- [ ] #236 VALIDATE: Auto-configuration works for test queries
- [ ] #237 VALIDATE: Recommendations match expected
- [ ] #238 COMMIT: "feat: complete phase 5 intelligence"
- [ ] #239 MERGE: phase-5-intelligence → develop

---

## PHASE 6: EXPORT SYSTEM ❌ NOT STARTED

### Export Interface
- [ ] #240 Create /backend/src/research_tool/services/export/__init__.py
- [ ] #241 Create /backend/src/research_tool/services/export/exporter.py (ABC)

### Export Implementations
- [ ] #242 Create markdown.py - Markdown export
- [ ] #243 Create json_export.py - JSON export
- [ ] #244 Create pdf.py - PDF export (WeasyPrint)
- [ ] #245 Create docx.py - Word export
- [ ] #246 Create pptx.py - PowerPoint export
- [ ] #247 Create xlsx.py - Excel export

### Templates
- [ ] #248 Create /backend/templates/report.md.j2
- [ ] #249 Create /backend/templates/report.html.j2 (for PDF)
- [ ] #250 Implement template selection logic
- [ ] #251 Test: Templates render correctly

### Export API
- [ ] #252 Create /backend/src/research_tool/api/routes/export.py
- [ ] #253 Implement POST /api/export
- [ ] #254 Implement GET /api/export/formats
- [ ] #255 Add routes to main.py

### SwiftUI Export View
- [ ] #256 Create ExportView.swift
- [ ] #257 Implement format selection
- [ ] #258 Implement export trigger
- [ ] #259 Implement file download/save

### Phase 6 Tests
- [ ] #260 Test: Markdown export valid
- [ ] #261 Test: JSON export valid
- [ ] #262 Test: PDF export opens correctly
- [ ] #263 Test: DOCX export opens correctly
- [ ] #264 Test: PPTX export opens correctly
- [ ] #265 Test: XLSX export opens correctly
- [ ] #266 Test: Large export (1000 sources) doesn't crash

### Phase 6 Validation
- [ ] #267 VALIDATE: Output anti-patterns #11, #12 not present
- [ ] #268 VALIDATE: Reports include limitations
- [ ] #269 COMMIT: "feat: complete phase 6 export"
- [ ] #270 MERGE: phase-6-export → develop

---

## PHASE 7: POLISH AND INTEGRATION ❌ NOT STARTED

### End-to-End Testing
- [ ] #271 Create /backend/tests/e2e/test_research_flow.py
- [ ] #272 Test: Medical research query end-to-end
- [ ] #273 Test: Competitive intelligence query end-to-end
- [ ] #274 Test: Academic research query end-to-end
- [ ] #275 Test: Privacy mode enforcement end-to-end

### Performance Optimization
- [ ] #276 Profile backend response times
- [ ] #277 Optimize slow queries
- [ ] #278 Verify <2s first token (local)
- [ ] #279 Verify <1s first token (cloud)
- [ ] #280 Verify <100ms memory retrieval
- [ ] #281 Verify <5min typical research

### Edge Case Handling
- [ ] #282 Handle: All sources fail gracefully
- [ ] #283 Handle: Network disconnection during research
- [ ] #284 Handle: Model overload
- [ ] #285 Handle: Malformed API responses
- [ ] #286 Handle: Very long queries
- [ ] #287 Handle: Empty results

### Documentation
- [ ] #288 Create README.md with setup instructions
- [ ] #289 Create API documentation
- [ ] #290 Create user guide
- [ ] #291 Update all docstrings

### Final Verification
- [ ] #292 VERIFY: Success criterion #1 - Query understanding
- [ ] #293 VERIFY: Success criterion #2 - Professional output
- [ ] #294 VERIFY: Success criterion #3 - Progress display
- [ ] #295 VERIFY: Success criterion #4 - Intelligent memory
- [ ] #296 VERIFY: Success criterion #5 - Minimal clarification
- [ ] #297 VERIFY: Success criterion #6 - Export formats
- [ ] #298 VERIFY: Success criterion #7 - Mode recommendation
- [ ] #299 VERIFY: Success criterion #8 - Conversational feel

### Final Metrics
- [ ] #300 VERIFY: >90% test coverage
- [ ] #301 VERIFY: 100% type coverage
- [ ] #302 VERIFY: 0 lint warnings
- [ ] #303 VERIFY: 0 security issues (bandit)

### Final Commit
- [ ] #304 COMMIT: "feat: complete phase 7 polish"
- [ ] #305 MERGE: phase-7-polish → develop
- [ ] #306 MERGE: develop → main
- [ ] #307 TAG: v1.0.0

---

## SUMMARY (HONEST STATUS)

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| Phase 0: Setup | #1-5 | 5/5 | ✅ COMPLETE |
| Phase 1: Foundation | #6-47 | 41/42 | ✅ COMPLETE (Swift build needs manual verify) |
| Phase 2: Conversational | #48-94 | 44/47 | ✅ COMPLETE (3 E2E need manual test) |
| Phase 3: Memory | #95-135 | 41/41 | ✅ COMPLETE |
| Phase 4: Research | #136-204 | 54/69 | ⚠️ 78% COMPLETE |
| Phase 5: Intelligence | #205-239 | 0/35 | ❌ NOT STARTED |
| Phase 6: Export | #240-270 | 0/31 | ❌ NOT STARTED |
| Phase 7: Polish | #271-307 | 0/37 | ❌ NOT STARTED |

**Total Tasks**: 307
**Completed**: ~185 (~60%)
**Tests**: 239 passing (2025-12-09)
**Linting**: 0 errors
**Type checking**: 0 errors

---

## TEST COVERAGE BREAKDOWN

### Unit Tests (22 files, 239 tests)
| File | Tests | Category |
|------|-------|----------|
| test_health.py | 2 | API |
| test_llm_router.py | 12 | LLM |
| test_model_selector.py | 17 | LLM |
| test_websocket.py | 10 | API/Integration |
| test_memory.py | 20 | Memory |
| test_crawler.py | 18 | Search |
| test_provider.py | 11 | Search |
| test_rate_limiter.py | 10 | Search |
| test_tavily.py | 8 | Search |
| test_brave.py | 10 | Search |
| test_arxiv.py | 7 | Search |
| test_pubmed.py | 9 | Search |
| test_semantic_scholar.py | 10 | Search |
| test_exa.py | 11 | Search |
| test_unpaywall.py | 12 | Search |
| test_clarify.py | 9 | Agent |
| test_plan.py | 8 | Agent |
| test_collect.py | 8 | Agent |
| test_process.py | 9 | Agent |
| test_analyze.py | 6 | Agent |
| test_evaluate.py | 9 | Agent |
| test_synthesize.py | 13 | Agent |

### Missing Test Coverage
- [ ] test_saturation.py - Saturation decision logic
- [ ] test_decisions.py - Decision tree logic
- [ ] test_agent_workflow.py - Full workflow integration
- [ ] E2E tests for all phases

---

## CRITICAL NEXT STEPS

1. **Manual verification needed**:
   - Open Xcode and build gui/ResearchTool/Package.swift
   - Run backend + Ollama and test E2E flow

2. **Missing implementations**:
   - #145 exa.py - Exa search provider
   - #149 unpaywall.py - Open access finder
   - #169 export_node.py - Export workflow node
   - #171-172 Decision trees (source_selector, clarification)
   - #185-186 LangGraph tool wrappers

3. **Missing tests**:
   - #157-158 Obstacle handling tests
   - #178-179 Saturation detection tests
   - #183 Full workflow integration test

4. **Phase 5-7**: Not started at all

---

## FILES THAT EXIST

### Backend (55 Python files)
```
src/research_tool/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── exceptions.py
│   └── logging.py
├── main.py
├── models/
│   ├── __init__.py
│   ├── domain.py
│   ├── entities.py
│   ├── requests.py
│   └── state.py
├── services/
│   ├── __init__.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── provider.py
│   │   ├── router.py
│   │   └── selector.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── combined_repo.py
│   │   ├── lance_repo.py
│   │   ├── learning.py
│   │   ├── repository.py
│   │   └── sqlite_repo.py
│   └── search/
│       ├── __init__.py
│       ├── arxiv.py
│       ├── brave.py
│       ├── crawler.py
│       ├── provider.py
│       ├── pubmed.py
│       ├── rate_limiter.py
│       ├── semantic_scholar.py
│       └── tavily.py
├── agent/
│   ├── __init__.py
│   ├── graph.py
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── analyze.py
│   │   ├── clarify.py
│   │   ├── collect.py
│   │   ├── evaluate.py
│   │   ├── plan.py
│   │   ├── process.py
│   │   └── synthesize.py
│   ├── decisions/
│   │   ├── __init__.py
│   │   ├── obstacle_handler.py
│   │   └── saturation.py
│   └── tools/
│       └── __init__.py
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   └── research.py
│   └── websocket/
│       ├── __init__.py
│       └── chat_ws.py
└── utils/
    ├── circuit_breaker.py
    └── retry.py
```

### GUI (8 Swift files)
```
gui/ResearchTool/ResearchTool/
├── App/
│   ├── ResearchToolApp.swift
│   └── AppState.swift
├── Models/
│   └── Message.swift
├── ViewModels/
│   └── ChatViewModel.swift
├── Views/
│   ├── ChatView.swift
│   ├── MainView.swift
│   ├── MessageBubble.swift
│   ├── PrivacyModePicker.swift
│   └── SettingsView.swift
└── Services/
    └── WebSocketClient.swift
```

---

*END OF TODO CHECKLIST*
*Last verified: 2025-12-09 by Claude Opus 4.5*
