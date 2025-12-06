# RESEARCH TOOL — TODO CHECKLIST
## Granular Task List for Claude Code Execution

**Instructions**: 
- Complete tasks in order
- Mark [x] when complete
- Commit after each numbered task
- If stuck on a task after 3 attempts, log in ERROR-LOG.md and skip

---

## PHASE 0: SETUP

### Repository Structure
- [ ] #1 Create directory structure per SPEC.md Section 2.2
- [ ] #2 Copy all documentation files to repository
- [ ] #3 Initialize git with develop branch
- [ ] #4 Create .gitignore for Python and Swift
- [ ] #5 Create .env.example with all required API keys

---

## PHASE 1: FOUNDATION

### Python Project Setup
- [ ] #6 Create /backend/pyproject.toml with all dependencies
- [ ] #7 Run `uv sync` to install dependencies
- [ ] #8 Verify imports: `python -c "import fastapi; import langgraph; import lancedb"`

### Core Configuration
- [ ] #9 Create /backend/src/research_tool/__init__.py
- [ ] #10 Create /backend/src/research_tool/core/__init__.py
- [ ] #11 Create /backend/src/research_tool/core/config.py (Settings class)
- [ ] #12 Create /backend/src/research_tool/core/exceptions.py (exception hierarchy)
- [ ] #13 Create /backend/src/research_tool/core/logging.py (structlog config)
- [ ] #14 Test: Import Settings and verify environment loading

### FastAPI Application
- [ ] #15 Create /backend/src/research_tool/main.py (FastAPI app)
- [ ] #16 Add /api/health endpoint
- [ ] #17 Add CORS middleware for SwiftUI
- [ ] #18 Add startup/shutdown events with logging
- [ ] #19 Test: Start server and hit health endpoint

### Test Framework
- [ ] #20 Create /backend/tests/__init__.py
- [ ] #21 Create /backend/tests/conftest.py (pytest fixtures)
- [ ] #22 Create /backend/tests/unit/__init__.py
- [ ] #23 Create /backend/tests/unit/test_health.py
- [ ] #24 Run: `pytest tests/ -v` - verify passing

### Linting and Type Checking
- [ ] #25 Create /backend/.pre-commit-config.yaml
- [ ] #26 Run: `ruff check .` - verify zero errors
- [ ] #27 Run: `mypy src/` - verify zero errors

### SwiftUI Project
- [ ] #28 Create Xcode project at /gui/ResearchTool/
- [ ] #29 Create ResearchToolApp.swift (app entry point)
- [ ] #30 Create AppState.swift (shared state)
- [ ] #31 Create MainView.swift (navigation structure)
- [ ] #32 Create ChatView.swift (chat interface)
- [ ] #33 Create MessageBubble.swift (message display)
- [ ] #34 Create SettingsView.swift (placeholder)
- [ ] #35 Create Message.swift (message model)
- [ ] #36 Create ChatViewModel.swift (chat logic - placeholder)
- [ ] #37 Build Xcode project - verify no errors

### Scripts
- [ ] #38 Create /scripts/setup.sh
- [ ] #39 Create /scripts/start_backend.sh
- [ ] #40 Create /scripts/start_ollama.sh
- [ ] #41 Create /scripts/run_tests.sh
- [ ] #42 Make all scripts executable: `chmod +x scripts/*.sh`

### Phase 1 Validation
- [ ] #43 VALIDATE: SwiftUI shows backend connection status
- [ ] #44 VALIDATE: All tests pass
- [ ] #45 VALIDATE: All linting passes
- [ ] #46 COMMIT: "feat: complete phase 1 foundation"
- [ ] #47 MERGE: phase-1-foundation → develop

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
- [x] #56 Test: Mock test for router

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
- [x] #75 Test: WebSocket connection test

### SwiftUI WebSocket Client
- [x] #76 Create /gui/.../Services/WebSocketClient.swift
- [x] #77 Implement connect() method
- [x] #78 Implement disconnect() method
- [x] #79 Implement send() method
- [x] #80 Implement message handlers (token, done, error)
- [x] #81 Update ChatViewModel to use WebSocket
- [x] #82 Update ChatView to show streaming response
- [x] #83 Add privacy mode selector to UI
- [x] #84 Build and test: Send message, receive streaming response

### Phase 2 Tests
- [x] #85 Create /backend/tests/unit/test_llm_router.py
- [x] #86 Create /backend/tests/unit/test_model_selector.py
- [x] #87 Create /backend/tests/integration/test_websocket.py
- [x] #88 Run: `pytest tests/ -v --cov` - verify >80% coverage (91%)

### Phase 2 Validation
- [ ] #89 VALIDATE: Local model responds correctly (requires Ollama)
- [ ] #90 VALIDATE: Cloud model responds correctly (requires API key)
- [x] #91 VALIDATE: LOCAL_ONLY never uses cloud (tested)
- [ ] #92 VALIDATE: Streaming works in GUI (requires E2E test)
- [x] #93 COMMIT: "feat: complete phase 2 conversational core"
- [ ] #94 MERGE: phase-2-conversational → develop (pending PR)

---

## PHASE 3: MEMORY SYSTEM

### Memory Repository Interface
- [ ] #95 Create /backend/src/research_tool/services/memory/__init__.py
- [ ] #96 Create /backend/src/research_tool/services/memory/repository.py (MemoryRepository ABC)
- [ ] #97 Define store_document() abstract method
- [ ] #98 Define search_similar() abstract method
- [ ] #99 Define get_source_effectiveness() abstract method
- [ ] #100 Define update_source_effectiveness() abstract method
- [ ] #101 Define record_access_failure() abstract method
- [ ] #102 Define is_known_failure() abstract method

### LanceDB Implementation
- [ ] #103 Create /backend/src/research_tool/services/memory/lance_repo.py
- [ ] #104 Define ResearchDocument LanceModel
- [ ] #105 Implement database connection
- [ ] #106 Implement store_document() - with embedding
- [ ] #107 Implement search_similar() - hybrid search
- [ ] #108 Implement chunking strategy (512 tokens, 64 overlap)
- [ ] #109 Test: Store and retrieve document

### SQLite Implementation
- [ ] #110 Create /backend/src/research_tool/services/memory/sqlite_repo.py
- [ ] #111 Define schema (from META guide Section 4.1.3)
- [ ] #112 Implement database initialization
- [ ] #113 Implement research_sessions CRUD
- [ ] #114 Implement source_effectiveness CRUD
- [ ] #115 Implement access_failures CRUD
- [ ] #116 Implement domain_config_overrides CRUD
- [ ] #117 Test: CRUD operations

### Source Effectiveness Learning
- [ ] #118 Create /backend/src/research_tool/services/memory/learning.py
- [ ] #119 Implement exponential moving average calculation
- [ ] #120 Implement update_effectiveness() method
- [ ] #121 Implement get_ranked_sources() method
- [ ] #122 Test: Effectiveness updates correctly

### Combined Memory Repository
- [ ] #123 Create composite repository combining Lance + SQLite
- [ ] #124 Implement unified interface
- [ ] #125 Test: All memory operations work together

### Phase 3 Tests
- [ ] #126 Create /backend/tests/unit/test_memory.py
- [ ] #127 Test: Vector storage and retrieval
- [ ] #128 Test: Structured data storage
- [ ] #129 Test: Memory persists across restarts
- [ ] #130 Test: Retrieval latency <100ms for 10K docs
- [ ] #131 Test: Source effectiveness tracking
- [ ] #132 Test: Access failure recording

### Phase 3 Validation
- [ ] #133 VALIDATE: Anti-patterns #8 and #9 not present
- [ ] #134 COMMIT: "feat: complete phase 3 memory system"
- [ ] #135 MERGE: phase-3-memory → develop

---

## PHASE 4: RESEARCH AGENT

### Data Models
- [ ] #136 Create /backend/src/research_tool/models/__init__.py
- [ ] #137 Create /backend/src/research_tool/models/state.py (ResearchState)
- [ ] #138 Create /backend/src/research_tool/models/domain.py (DomainConfiguration)
- [ ] #139 Create /backend/src/research_tool/models/entities.py (Entity, Fact, SourceResult)
- [ ] #140 Create /backend/src/research_tool/models/requests.py (API models)

### Search Provider Interface
- [ ] #141 Create /backend/src/research_tool/services/search/__init__.py
- [ ] #142 Create /backend/src/research_tool/services/search/provider.py (SearchProvider ABC)
- [ ] #143 Create /backend/src/research_tool/services/search/rate_limiter.py

### Search Provider Implementations
- [ ] #144 Create tavily.py - Tavily search provider
- [ ] #145 Create exa.py - Exa search provider
- [ ] #146 Create semantic_scholar.py - with 1 RPS rate limit
- [ ] #147 Create pubmed.py - PubMed provider
- [ ] #148 Create arxiv.py - arXiv provider
- [ ] #149 Create unpaywall.py - Open access finder
- [ ] #150 Create brave.py - Brave search provider
- [ ] #151 Create crawler.py - Playwright with stealth
- [ ] #152 Test: Each provider returns results

### Obstacle Handling
- [ ] #153 Create /backend/src/research_tool/utils/retry.py (tenacity config)
- [ ] #154 Create /backend/src/research_tool/utils/circuit_breaker.py
- [ ] #155 Implement exponential backoff (4s, 8s, 16s, 32s, 60s max)
- [ ] #156 Implement proxy rotation (if needed)
- [ ] #157 Test: Rate limit triggers backoff
- [ ] #158 Test: Circuit breaker opens after failures

### LangGraph Agent
- [ ] #159 Create /backend/src/research_tool/agent/__init__.py
- [ ] #160 Create /backend/src/research_tool/agent/graph.py (StateGraph setup)
- [ ] #161 Create /backend/src/research_tool/agent/nodes/__init__.py

### Agent Nodes
- [ ] #162 Create clarify.py - Query clarification node
- [ ] #163 Create plan.py - Research planning node
- [ ] #164 Create collect.py - Data collection node
- [ ] #165 Create process.py - Data processing node
- [ ] #166 Create analyze.py - Analysis node
- [ ] #167 Create evaluate.py - Saturation evaluation node
- [ ] #168 Create synthesize.py - Synthesis node
- [ ] #169 Create export_node.py - Export node

### Decision Logic
- [ ] #170 Create /backend/src/research_tool/agent/decisions/__init__.py
- [ ] #171 Create source_selector.py (decision tree from META 7.2)
- [ ] #172 Create clarification.py (decision tree from META 7.3)
- [ ] #173 Create obstacle_handler.py (decision tree from META 7.4)
- [ ] #174 Create saturation.py (decision tree from META 7.5)

### Saturation Detection
- [ ] #175 Implement SaturationMetrics dataclass
- [ ] #176 Implement calculate_saturation() function
- [ ] #177 Implement should_stop() function
- [ ] #178 Test: Saturation detected at threshold
- [ ] #179 Test: Research continues below threshold

### Graph Assembly
- [ ] #180 Wire all nodes in graph.py
- [ ] #181 Add conditional edges
- [ ] #182 Add checkpointing
- [ ] #183 Test: Complete workflow executes

### Agent Tools
- [ ] #184 Create /backend/src/research_tool/agent/tools/__init__.py
- [ ] #185 Create search_tool.py - LangGraph tool wrapper
- [ ] #186 Create memory_tool.py - Memory access tool
- [ ] #187 Test: Tools integrate with agent

### Research API
- [ ] #188 Create /backend/src/research_tool/api/routes/research.py
- [ ] #189 Implement POST /api/research/start
- [ ] #190 Implement GET /api/research/{id}/status
- [ ] #191 Implement POST /api/research/{id}/approve
- [ ] #192 Implement POST /api/research/{id}/stop
- [ ] #193 Create progress WebSocket handler
- [ ] #194 Add routes to main.py

### Phase 4 Tests
- [ ] #195 Create /backend/tests/unit/test_search_providers.py
- [ ] #196 Create /backend/tests/unit/test_saturation.py
- [ ] #197 Create /backend/tests/unit/test_decisions.py
- [ ] #198 Create /backend/tests/integration/test_agent_workflow.py
- [ ] #199 Test: Full research cycle on test query

### Phase 4 Validation
- [ ] #200 VALIDATE: Search anti-patterns #3, #4, #5 not present
- [ ] #201 VALIDATE: Obstacle anti-patterns #6, #7 not present
- [ ] #202 VALIDATE: Audit trail captures all decisions
- [ ] #203 COMMIT: "feat: complete phase 4 research agent"
- [ ] #204 MERGE: phase-4-research → develop

---

## PHASE 5: INTELLIGENCE FEATURES

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

## PHASE 6: EXPORT SYSTEM

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

## PHASE 7: POLISH AND INTEGRATION

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

## SUMMARY

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 0: Setup | #1-5 | [ ] |
| Phase 1: Foundation | #6-47 | [ ] |
| Phase 2: Conversational | #48-94 | [ ] |
| Phase 3: Memory | #95-135 | [ ] |
| Phase 4: Research | #136-204 | [ ] |
| Phase 5: Intelligence | #205-239 | [ ] |
| Phase 6: Export | #240-270 | [ ] |
| Phase 7: Polish | #271-307 | [ ] |

**Total Tasks**: 307

---

*END OF TODO CHECKLIST*
