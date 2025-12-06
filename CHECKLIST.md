# VALIDATION CHECKLIST
## Phase Completion and Quality Verification

**Instructions**: Complete ALL items for each phase before merging.

---

## PRE-BUILD CHECKLIST

Before starting any coding:

```
□ Repository initialized at correct location
□ All documentation files in place
□ .gitignore configured for Python and Swift
□ .env.example created with all required keys
□ develop branch created
□ META-BUILD-GUIDE-v2.md in /docs/
```

---

## PHASE 1: FOUNDATION

### Code Quality
```
□ All Python files have module docstrings
□ All functions have type hints
□ All public functions have docstrings
□ ruff check . passes with 0 errors
□ mypy src/ passes with 0 errors
```

### Functionality
```
□ Backend starts without errors: uvicorn research_tool.main:app
□ Health endpoint responds: curl localhost:8000/api/health
□ SwiftUI project builds without errors
□ SwiftUI app launches and displays UI
□ Connection indicator shows backend status correctly
```

### Tests
```
□ pytest runs without configuration errors
□ test_health.py passes
□ Coverage report generates
```

### Integration
```
□ SwiftUI can reach backend health endpoint
□ Backend logs requests correctly
□ No hardcoded paths that won't work on target machine
```

### Documentation
```
□ README.md exists with setup instructions
□ All scripts are executable
□ .env.example documents all required variables
```

### Commit
```
□ All changes committed
□ Commit message follows convention
□ Branch merged to develop
```

---

## PHASE 2: CONVERSATIONAL CORE

### Code Quality
```
□ All new files have module docstrings
□ All new functions have type hints and docstrings
□ ruff check . passes with 0 errors
□ mypy src/ passes with 0 errors
□ No code violates Anti-Pattern #10 (privacy mode)
```

### LLM Router
```
□ LLMRouter class implemented
□ complete() method works with streaming
□ complete() method works without streaming
□ Fallback logic implemented
□ is_model_available() method works
```

### Model Selector
```
□ PrivacyMode enum defined correctly
□ TaskComplexity enum defined correctly
□ select() method implements decision tree from META guide 7.1
□ LOCAL_ONLY NEVER returns cloud model (test this!)
□ recommend_privacy_mode() detects sensitive keywords
```

### WebSocket
```
□ WebSocket connection establishes
□ Messages received and parsed correctly
□ Streaming tokens sent individually
□ Conversation history maintained
□ Errors sent to client appropriately
```

### SwiftUI
```
□ WebSocketClient connects to backend
□ Messages display in chat view
□ Streaming tokens append in real-time
□ Privacy mode selector works
□ Model used is displayed to user
```

### Tests
```
□ test_llm_router.py exists and passes
□ test_model_selector.py exists and passes
□ test_local_only_never_selects_cloud passes
□ test_sensitive_keywords_trigger_local_only passes
□ Integration test for WebSocket passes
□ Coverage >80% for new code
```

### Performance
```
□ First token latency <2s for local model
□ First token latency <1s for cloud model
□ Streaming feels responsive in GUI
```

### Commit
```
□ All changes committed
□ Commit message follows convention
□ Branch merged to develop
```

---

## PHASE 3: MEMORY SYSTEM

### Code Quality
```
□ All new files have docstrings and type hints
□ ruff and mypy pass
□ No code violates Anti-Patterns #8 or #9
```

### LanceDB
```
□ Database creates successfully
□ Documents store with embeddings
□ Hybrid search returns relevant results
□ Chunking produces correct size chunks
```

### SQLite
```
□ Schema creates all tables
□ research_sessions CRUD works
□ source_effectiveness CRUD works
□ access_failures CRUD works
□ domain_config_overrides CRUD works
```

### Learning
```
□ Effectiveness scores update correctly
□ Exponential moving average calculated correctly
□ Scores persist across restarts
```

### Combined Repository
```
□ Unified interface works
□ Vector and structured operations compose correctly
```

### Tests
```
□ test_memory.py exists and passes
□ Vector storage and retrieval tested
□ Persistence across restart tested
□ Retrieval latency <100ms for 10K docs (benchmark test)
□ Coverage >80% for new code
```

### Commit
```
□ All changes committed
□ Branch merged to develop
```

---

## PHASE 4: RESEARCH AGENT

### Code Quality
```
□ All files documented and typed
□ ruff and mypy pass
□ No Anti-Patterns #3, #4, #5, #6, #7 present
```

### Data Models
```
□ ResearchState defined per META guide 4.1
□ DomainConfiguration defined correctly
□ Entity, Fact, SourceResult defined correctly
```

### Search Providers
```
□ SearchProvider interface implemented
□ Tavily provider works
□ Exa provider works
□ Semantic Scholar provider works (with rate limiting!)
□ PubMed provider works
□ arXiv provider works
□ Unpaywall provider works
□ Brave provider works
□ Playwright crawler works with stealth
```

### Rate Limiting
```
□ RateLimiter class implemented
□ Semantic Scholar limited to 1 RPS
□ Exponential backoff works
□ Rate limit errors trigger retry
```

### Obstacle Handling
```
□ Rate limit handling per decision tree
□ CAPTCHA handling (if service enabled)
□ Paywall handling with Unpaywall fallback
□ Access denied recorded permanently
□ Timeout with retry
□ Circuit breaker prevents cascade failures
```

### LangGraph Agent
```
□ StateGraph defined correctly
□ All nodes implemented
□ Conditional edges work
□ Checkpointing enabled
□ Human-in-loop works (approval step)
```

### Saturation Detection
```
□ SaturationMetrics calculated correctly
□ should_stop() returns true at threshold
□ should_stop() returns false below threshold
□ Stopping reason logged in plain language
```

### API
```
□ POST /api/research/start works
□ GET /api/research/{id}/status works
□ POST /api/research/{id}/approve works
□ POST /api/research/{id}/stop works
□ WebSocket progress streaming works
```

### Tests
```
□ test_search_providers.py passes
□ test_saturation.py passes
□ test_decisions.py passes
□ test_agent_workflow.py passes
□ Full research cycle completes on test query
□ Coverage >80%
```

### Commit
```
□ All changes committed
□ Branch merged to develop
```

---

## PHASE 5: INTELLIGENCE FEATURES

### Code Quality
```
□ All files documented and typed
□ ruff and mypy pass
```

### Domain Detection
```
□ Detects medical domain correctly
□ Detects competitive intelligence correctly
□ Detects regulatory correctly
□ Detects academic correctly
□ Unknown domains handled gracefully
```

### Auto-Configuration
```
□ Domain configs load from JSON
□ Learned overrides merge correctly
□ Correct config selected for domain
```

### Cross-Verification
```
□ Facts extracted from sources
□ Cross-source comparison works
□ Contradictions detected
□ Verification status set correctly
```

### Confidence Scoring
```
□ Source-based confidence calculated
□ Verification-based confidence calculated
□ Composite score makes sense
□ Scores correlate with actual quality
```

### Learning
```
□ Source effectiveness updates after research
□ Domain configs update with discovered sources
□ Learning persists to next research
□ Past research influences future planning
```

### Privacy Recommendation
```
□ Sensitive content detected
□ Recommendations include reasoning
□ Recommendations match expected for test cases
```

### Tests
```
□ Domain detection >90% accuracy
□ Contradictions detected in test data
□ Learning influences future research (verified)
□ Coverage >80%
```

### Commit
```
□ All changes committed
□ Branch merged to develop
```

---

## PHASE 6: EXPORT SYSTEM

### Code Quality
```
□ All files documented and typed
□ ruff and mypy pass
□ No Anti-Patterns #11 or #12 present
```

### Export Formats
```
□ Markdown export valid
□ JSON export valid
□ PDF export opens correctly
□ DOCX export opens correctly
□ PPTX export opens correctly
□ XLSX export opens correctly
```

### Templates
```
□ Jinja2 templates render correctly
□ Template selection based on context
□ Templates include all required sections
```

### Report Quality
```
□ Reports include what was found
□ Reports include what was NOT found
□ Reports include stopping rationale
□ Reports include confidence levels
□ Reports include access failures
```

### API
```
□ POST /api/export works
□ GET /api/export/formats works
□ Export files downloadable
```

### SwiftUI
```
□ Export view allows format selection
□ Export triggers correctly
□ Files save/download correctly
```

### Tests
```
□ Each format produces valid file
□ Large export (1000 sources) doesn't crash
□ Report includes limitations (tested)
□ Coverage >80%
```

### Commit
```
□ All changes committed
□ Branch merged to develop
```

---

## PHASE 7: POLISH AND INTEGRATION

### End-to-End Tests
```
□ Medical research query completes
□ Competitive intelligence query completes
□ Academic research query completes
□ Privacy mode enforced end-to-end
```

### Performance
```
□ First token <2s (local)
□ First token <1s (cloud)
□ Memory retrieval <100ms
□ Typical research <5min
```

### Edge Cases
```
□ All sources fail → graceful degradation
□ Network disconnect → handled
□ Model overload → handled
□ Malformed responses → handled
□ Very long queries → handled
□ Empty results → handled
```

### Documentation
```
□ README.md complete with setup instructions
□ API documentation complete
□ User guide complete
□ All docstrings complete
```

### Final Metrics
```
□ Test coverage >90%
□ Type coverage 100%
□ Lint warnings: 0
□ Security issues (bandit): 0
```

### Success Criteria (from META guide Section 1.1)
```
□ #1: Plain language query → understanding + clarification
□ #2: Professional service level output
□ #3: Real-time progress in plain language
□ #4: Intelligent memory use
□ #5: Asks only when genuinely needed
□ #6: Export suited to next step
□ #7: Recommends local/cloud/hybrid
□ #8: Conversational feel
```

### Final Anti-Pattern Check
```
□ #1 (unnecessary questions) - NOT present
□ #2 (clarification escape hatch) - NOT present
□ #3 (stopping too early) - NOT present
□ #4 (stopping too late) - NOT present
□ #5 (ignoring source quality) - NOT present
□ #6 (silent failure) - NOT present
□ #7 (infinite retry) - NOT present
□ #8 (not using memory for planning) - NOT present
□ #9 (not updating memory after research) - NOT present
□ #10 (ignoring privacy mode) - NOT present
□ #11 (omitting what wasn't found) - NOT present
□ #12 (not explaining stopping rationale) - NOT present
```

### Final Commit
```
□ All changes committed
□ Branch merged to develop
□ develop merged to main
□ Tagged v1.0.0
□ Pushed to GitHub
```

---

## POST-BUILD CHECKLIST

After v1.0.0 release:

```
□ User acceptance testing completed
□ All feedback addressed
□ Documentation reviewed for accuracy
□ Repository cleaned (no temp files, no .env with real keys)
□ Final backup made
```

---

*END OF VALIDATION CHECKLIST*
