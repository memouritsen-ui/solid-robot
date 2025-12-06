# RESEARCH TOOL — SPECIFICATION
## Master Specification for Claude Code Autonomous Build

**Repository**: https://github.com/memouritsen-ui/solid-robot.git
**Local Workspace**: /Users/madsbruusgaard-mouritsen/solid-robot
**Constitutional Authority**: META-BUILD-GUIDE-v2.md (located in /docs/)

---

## DOCUMENT HIERARCHY

```
AUTHORITY LEVEL 1: META-BUILD-GUIDE-v2.md
    ↓ (defines requirements, decisions, patterns)
AUTHORITY LEVEL 2: SPEC.md (this file)
    ↓ (operationalizes META guide for this build)
AUTHORITY LEVEL 3: BUILD-PLAN.md
    ↓ (step-by-step execution instructions)
AUTHORITY LEVEL 4: TODO.md
    ↓ (granular task checklist)
AUTHORITY LEVEL 5: Phase docs (/docs/phase-X.md)
    ↓ (detailed implementation guidance)
```

**RULE**: Higher authority documents override lower. If conflict exists, escalate to user.

---

## 1. PROJECT OVERVIEW

### 1.1 What We Are Building

A professional-grade research assistant tool with:
- **SwiftUI native macOS GUI** — Conversational interface
- **Python/FastAPI backend** — Agent logic and API handling
- **LangGraph research agent** — Single ReAct agent with specialized tools
- **Persistent memory** — LanceDB vectors + SQLite structured data
- **Professional OSINT methodology** — Intelligence cycle with saturation detection
- **Multi-model support** — Local (Ollama) and cloud (Claude API) via LiteLLM

### 1.2 Target Environment

| Attribute | Value |
|-----------|-------|
| Machine | M4 Max MacBook Pro, 48GB RAM |
| OS | macOS (latest) |
| Python | 3.11+ (via uv) |
| Swift | Latest Xcode |
| Local LLM | Ollama (native, NOT Docker) |
| Package Manager | uv (Python), Swift Package Manager (Swift) |

### 1.3 Success Criteria

From META guide Section 1.1 — ALL must be satisfied:

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | Plain language query → understanding + clarification | Test with 10 ambiguous queries |
| 2 | Professional service level output | Benchmark against CI firm deliverables |
| 3 | Real-time progress in plain language | GUI shows status updates |
| 4 | Intelligent memory use | Memory retrieval logged + influences decisions |
| 5 | Asks only when genuinely needed | Clarification requests logged with justification |
| 6 | Export suited to next step | Each format validated |
| 7 | Recommends local/cloud/hybrid | Recommendation logged with reasoning |
| 8 | Conversational feel | User assessment |

---

## 2. ARCHITECTURE SPECIFICATION

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        SwiftUI GUI                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Chat View   │  │ Progress    │  │ Settings/Export         │  │
│  │             │  │ Panel       │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ WebSocket + REST (localhost:8000)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Python Backend (FastAPI)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Chat API    │  │ Research    │  │ Export API              │  │
│  │             │  │ API         │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Core Services Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ LiteLLM     │  │ LangGraph   │  │ Memory                  │  │
│  │ Router      │  │ Agent       │  │ Repository              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     External Integrations                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Ollama      │  │ Search APIs │  │ Storage                 │  │
│  │ (local LLM) │  │ (Tavily,etc)│  │ (LanceDB, SQLite)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Directory Structure

```
solid-robot/
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI pipeline
├── docs/
│   ├── META-BUILD-GUIDE-v2.md        # Constitutional authority
│   ├── phase-1-foundation.md
│   ├── phase-2-conversational.md
│   ├── phase-3-memory.md
│   ├── phase-4-research.md
│   ├── phase-5-intelligence.md
│   ├── phase-6-export.md
│   └── phase-7-polish.md
├── gui/
│   ├── ResearchTool/
│   │   ├── ResearchTool.xcodeproj/
│   │   ├── ResearchTool/
│   │   │   ├── App/
│   │   │   │   ├── ResearchToolApp.swift
│   │   │   │   └── AppState.swift
│   │   │   ├── Views/
│   │   │   │   ├── MainView.swift
│   │   │   │   ├── ChatView.swift
│   │   │   │   ├── MessageBubble.swift
│   │   │   │   ├── ProgressPanel.swift
│   │   │   │   ├── SettingsView.swift
│   │   │   │   └── ExportView.swift
│   │   │   ├── ViewModels/
│   │   │   │   ├── ChatViewModel.swift
│   │   │   │   ├── ResearchViewModel.swift
│   │   │   │   └── SettingsViewModel.swift
│   │   │   ├── Services/
│   │   │   │   ├── APIClient.swift
│   │   │   │   ├── WebSocketClient.swift
│   │   │   │   └── BackendHealthCheck.swift
│   │   │   ├── Models/
│   │   │   │   ├── Message.swift
│   │   │   │   ├── ResearchStatus.swift
│   │   │   │   └── Settings.swift
│   │   │   └── Resources/
│   │   │       └── Assets.xcassets/
│   │   └── ResearchToolTests/
│   │       ├── ViewModelTests/
│   │       └── ServiceTests/
│   └── Package.swift                 # If using SPM
├── backend/
│   ├── pyproject.toml
│   ├── src/
│   │   └── research_tool/
│   │       ├── __init__.py
│   │       ├── main.py               # FastAPI entry point
│   │       ├── api/
│   │       │   ├── __init__.py
│   │       │   ├── routes/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── chat.py
│   │       │   │   ├── research.py
│   │       │   │   └── export.py
│   │       │   ├── websocket/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── chat_ws.py
│   │       │   │   └── progress_ws.py
│   │       │   └── middleware/
│   │       │       ├── __init__.py
│   │       │       └── error_handler.py
│   │       ├── core/
│   │       │   ├── __init__.py
│   │       │   ├── config.py         # Settings management
│   │       │   ├── exceptions.py     # Exception hierarchy
│   │       │   └── logging.py        # Structured logging
│   │       ├── models/
│   │       │   ├── __init__.py
│   │       │   ├── state.py          # ResearchState, etc.
│   │       │   ├── domain.py         # DomainConfiguration
│   │       │   ├── entities.py       # Entity, Fact, SourceResult
│   │       │   └── requests.py       # API request/response models
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── llm/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── provider.py   # ModelProvider interface
│   │       │   │   ├── router.py     # LiteLLM Router
│   │       │   │   └── selector.py   # Model selection logic
│   │       │   ├── search/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── provider.py   # SearchProvider interface
│   │       │   │   ├── tavily.py
│   │       │   │   ├── exa.py
│   │       │   │   ├── semantic_scholar.py
│   │       │   │   ├── pubmed.py
│   │       │   │   ├── arxiv.py
│   │       │   │   ├── unpaywall.py
│   │       │   │   ├── brave.py
│   │       │   │   ├── crawler.py    # Crawl4AI/Playwright
│   │       │   │   └── rate_limiter.py
│   │       │   ├── memory/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── repository.py # MemoryRepository interface
│   │       │   │   ├── lance_repo.py # LanceDB implementation
│   │       │   │   ├── sqlite_repo.py# SQLite implementation
│   │       │   │   └── learning.py   # Source effectiveness tracking
│   │       │   └── export/
│   │       │       ├── __init__.py
│   │       │       ├── exporter.py   # Exporter interface
│   │       │       ├── markdown.py
│   │       │       ├── json_export.py
│   │       │       ├── pdf.py
│   │       │       ├── docx.py
│   │       │       ├── pptx.py
│   │       │       └── xlsx.py
│   │       ├── agent/
│   │       │   ├── __init__.py
│   │       │   ├── graph.py          # LangGraph workflow
│   │       │   ├── nodes/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── clarify.py
│   │       │   │   ├── plan.py
│   │       │   │   ├── collect.py
│   │       │   │   ├── process.py
│   │       │   │   ├── analyze.py
│   │       │   │   ├── evaluate.py
│   │       │   │   ├── synthesize.py
│   │       │   │   └── export_node.py
│   │       │   ├── tools/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── search_tool.py
│   │       │   │   ├── memory_tool.py
│   │       │   │   └── export_tool.py
│   │       │   └── decisions/
│   │       │       ├── __init__.py
│   │       │       ├── model_selector.py
│   │       │       ├── source_selector.py
│   │       │       ├── clarification.py
│   │       │       ├── obstacle_handler.py
│   │       │       └── saturation.py
│   │       └── utils/
│   │           ├── __init__.py
│   │           ├── retry.py          # Retry with backoff
│   │           ├── circuit_breaker.py
│   │           └── validators.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # Pytest fixtures
│   │   ├── unit/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_llm_router.py
│   │   │   ├── test_search_providers.py
│   │   │   ├── test_memory.py
│   │   │   ├── test_saturation.py
│   │   │   └── test_decisions.py
│   │   ├── integration/
│   │   │   ├── __init__.py
│   │   │   ├── test_agent_workflow.py
│   │   │   ├── test_api_endpoints.py
│   │   │   └── test_websocket.py
│   │   └── e2e/
│   │       ├── __init__.py
│   │       └── test_research_flow.py
│   ├── templates/
│   │   ├── report.html.j2
│   │   ├── report.md.j2
│   │   └── slides.pptx.j2
│   └── data/
│       └── domain_configs/
│           ├── medical.json
│           ├── competitive_intelligence.json
│           ├── regulatory.json
│           └── academic.json
├── scripts/
│   ├── setup.sh                      # Full setup script
│   ├── start_backend.sh
│   ├── start_ollama.sh
│   └── run_tests.sh
├── SPEC.md                           # This file
├── BUILD-PLAN.md
├── TODO.md
├── CHECKLIST.md
├── CLAUDE-CODE-INSTRUCTIONS.md
├── ERROR-HANDLING.md
├── MERGELOG.md
├── DECISIONS.md                      # Runtime decisions log
├── .env.example
├── .gitignore
└── README.md
```

### 2.3 Technology Stack (Locked)

From META guide Section 2.1-2.4:

| Layer | Technology | Version/Config |
|-------|------------|----------------|
| GUI Framework | SwiftUI | Latest Xcode |
| Backend Framework | FastAPI | 0.100+ |
| Agent Framework | LangGraph | Latest |
| Model Orchestration | LiteLLM | Latest |
| Local LLM | Ollama (native) | Latest |
| Vector DB | LanceDB | Latest |
| Structured DB | SQLite | 3.x |
| Graph Operations | NetworkX | 3.x |
| Primary Model (local) | Qwen2.5-32B-Instruct Q5_K_M | Via Ollama |
| Fast Model (local) | Llama-3.1-8B Q8_0 | Via Ollama |
| Cloud Model | Claude API | claude-3-5-sonnet |

**DO NOT SUBSTITUTE** any technology without user approval.

---

## 3. INTERFACE CONTRACTS

### 3.1 Backend API Endpoints

```
POST   /api/chat/message          # Send chat message
GET    /api/chat/history          # Get conversation history
WS     /ws/chat                   # Streaming chat

POST   /api/research/start        # Start research task
GET    /api/research/{id}/status  # Get research status
POST   /api/research/{id}/approve # Approve research plan
POST   /api/research/{id}/stop    # Stop research
WS     /ws/research/{id}          # Stream research progress

POST   /api/export                # Export research results
GET    /api/export/formats        # List available formats

GET    /api/settings              # Get current settings
PUT    /api/settings              # Update settings
GET    /api/health                # Health check
```

### 3.2 WebSocket Message Types

```typescript
// Chat WebSocket
interface ChatMessage {
  type: "user" | "assistant" | "token" | "done" | "error";
  content?: string;
  timestamp: string;
}

// Research WebSocket
interface ProgressMessage {
  type: "phase_started" | "phase_completed" | "source_queried" | 
        "obstacle_encountered" | "obstacle_resolved" | 
        "saturation_update" | "user_input_needed" | "error";
  message: string;        // Plain language for display
  details: object;        // Structured data for logging
  timestamp: string;
}
```

### 3.3 Data Models

See META guide Section 4.1 for complete data structures. Key models:

- `ResearchState` — Agent state throughout workflow
- `SourceResult` — Single search result
- `Entity` — Extracted entity with sources
- `Fact` — Verified fact with confidence
- `DomainConfiguration` — Per-domain source configuration
- `SaturationMetrics` — Stopping decision metrics

---

## 4. BEHAVIORAL REQUIREMENTS

### 4.1 Query Clarification Behavior

From META guide Section 7.3:

1. Attempt to proceed with reasonable interpretation
2. Ask ONLY if genuinely blocked
3. Maximum 2 clarifying exchanges before starting
4. Log all clarification requests with justification

**Anti-patterns to prevent** (META guide Section 5.1):
- Asking unnecessary questions
- Using clarification as escape hatch

### 4.2 Search Execution Behavior

From META guide Section 7.2:

1. Load domain configuration from memory
2. Get source effectiveness scores
3. Sort sources by priority × effectiveness
4. Query in order with rate limiting
5. Handle obstacles per decision tree
6. Check saturation after each cycle

**Anti-patterns to prevent** (META guide Section 5.2):
- Stopping too early (before saturation)
- Stopping too late (wasting resources)
- Ignoring source quality scores

### 4.3 Memory Behavior

From META guide Section 5.4:

1. ALWAYS consult memory before planning
2. ALWAYS update memory after research
3. Track source effectiveness with exponential moving average
4. Record access failures permanently

### 4.4 Privacy Mode Behavior

From META guide Section 7.1:

1. LOCAL_ONLY: Never call cloud API
2. CLOUD_ALLOWED: Can use any model
3. HYBRID: Specific rules per data type
4. Always explain recommendation reasoning

### 4.5 Output Behavior

From META guide Section 5.6:

1. Always include what was NOT found
2. Always explain stopping rationale
3. Include confidence levels
4. Include access failures and reasons

---

## 5. TESTING REQUIREMENTS

### 5.1 Coverage Targets

| Category | Target | Tool |
|----------|--------|------|
| Unit tests | 90% line coverage | pytest-cov |
| Type coverage | 100% | mypy --strict |
| Integration tests | All interfaces | pytest |
| E2E tests | Critical paths | pytest |

### 5.2 Required Test Cases

**Query Clarification**:
- Ambiguous query → proceeds with reasonable interpretation
- Genuinely blocking ambiguity → asks ONE focused question
- Clarification request logged with justification

**Search Execution**:
- Rate limit → backoff and retry
- Source failure → fallback to next source
- All sources fail → clear report to user
- Saturation threshold → stops with explanation

**Memory**:
- Similar past research influences planning
- Source effectiveness updates after research
- Access failures permanently recorded

**Privacy Mode**:
- LOCAL_ONLY never calls cloud API
- Recommendation includes reasoning

**Output**:
- Report includes limitations section
- Report includes stopping rationale
- Each export format produces valid file

### 5.3 Performance Benchmarks

| Metric | Target |
|--------|--------|
| First token (local) | <2s |
| First token (cloud) | <1s |
| Memory retrieval | <100ms for 10K docs |
| Typical research | <5min |

---

## 6. ACCEPTANCE CRITERIA

The build is COMPLETE when:

1. [ ] All 8 success criteria verified with evidence
2. [ ] All anti-patterns verified NOT present
3. [ ] All tests passing with coverage targets met
4. [ ] All performance benchmarks met
5. [ ] User can complete full research task without assistance
6. [ ] Memory and learning verified across multiple tasks
7. [ ] All export formats produce valid, openable files
8. [ ] Documentation complete (README, API docs)

---

## 7. CONSTRAINTS

### 7.1 Absolute Constraints

- **DO NOT** use Docker for Ollama (breaks Metal GPU)
- **DO NOT** use multi-agent architecture
- **DO NOT** substitute technologies without user approval
- **DO NOT** skip tests before implementation (TDD mandatory)
- **DO NOT** ignore rate limits
- **DO NOT** fail silently — always log and report

### 7.2 Quality Constraints

- Zero lint warnings (ruff)
- Zero type errors (mypy strict)
- Zero security issues (bandit)
- All functions have docstrings
- All functions have type hints

---

## 8. DOCUMENT REFERENCES

| Document | Purpose | Location |
|----------|---------|----------|
| META-BUILD-GUIDE-v2.md | Constitutional authority | /docs/ |
| BUILD-PLAN.md | Step-by-step execution | / |
| TODO.md | Granular task checklist | / |
| CHECKLIST.md | Validation checklist | / |
| CLAUDE-CODE-INSTRUCTIONS.md | Autonomous operation rules | / |
| ERROR-HANDLING.md | Recovery procedures | / |
| phase-X.md | Phase implementation details | /docs/ |

---

*END OF SPECIFICATION*
