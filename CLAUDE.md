# CLAUDE.md - Research Tool Project

## MANDATORY RULES

### Before ANY code change:
```bash
cd backend && uv run ruff check src/ tests/
cd backend && uv run python -m mypy src/ --ignore-missing-imports
cd backend && uv run python -m pytest tests/ -v
```
ALL must pass. No exceptions.

### Test requirements:
- 216 tests must pass
- 0 ruff errors
- 0 mypy errors
- Write tests BEFORE claiming something works

### Do NOT:
- Claim something is "done" without running tests
- Create placeholder/stub implementations
- Skip writing tests for new code
- Mark TODO items complete without verification

---

## PROJECT STRUCTURE

```
solid-robot/
├── backend/           # Python FastAPI backend
│   ├── src/research_tool/
│   │   ├── agent/     # LangGraph research agent
│   │   ├── api/       # REST + WebSocket endpoints
│   │   ├── core/      # Config, exceptions, logging
│   │   ├── models/    # Pydantic models
│   │   ├── services/  # LLM, Memory, Search
│   │   └── utils/     # Retry, circuit breaker
│   └── tests/         # pytest tests (216 tests)
├── gui/               # SwiftUI macOS app
│   └── ResearchTool/
└── scripts/           # Shell scripts
```

---

## VERIFICATION COMMANDS

```bash
# Run ALL before claiming anything works:
cd /Users/madsbruusgaard-mouritsen/solid-robot/backend

# Tests (must show "216 passed")
uv run python -m pytest tests/ -v

# Linting (must show "All checks passed!")
uv run ruff check src/ tests/

# Type checking (must show "Success")
uv run python -m mypy src/ --ignore-missing-imports

# Swift (manual in Xcode)
# Open gui/ResearchTool/Package.swift and build
```

---

## CURRENT STATUS

- Phase 0-3: COMPLETE
- Phase 4: 75% complete (missing exa.py, unpaywall.py, export_node.py, decision trees)
- Phase 5-7: NOT STARTED

See TODO.md for complete task breakdown.

---

## KEY FILES

### Backend entry:
- `backend/src/research_tool/main.py` - FastAPI app

### Agent nodes:
- `backend/src/research_tool/agent/nodes/*.py` - clarify, plan, collect, process, analyze, evaluate, synthesize

### Search providers:
- `backend/src/research_tool/services/search/*.py` - tavily, brave, arxiv, pubmed, semantic_scholar, crawler

### Tests:
- `backend/tests/unit/` - 20 test files, 216 tests

---

## ANTI-PATTERNS TO AVOID

1. Do NOT claim code works without running tests
2. Do NOT create empty implementations
3. Do NOT skip test coverage
4. Do NOT mark TODOs complete without verification
5. Do NOT trust file existence = working code

---

## HOW TO CONTINUE DEVELOPMENT

1. Read TODO.md for next tasks
2. Pick an uncompleted task
3. Write test FIRST
4. Implement code
5. Run ALL verification commands
6. Only mark complete when ALL pass

---

*This file enforces quality. Follow it.*
