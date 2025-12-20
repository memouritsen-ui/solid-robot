# CLAUDE.md - SOLID-ROBOT Professional Research Scraper

## CURRENT STATUS (Updated 2025-12-20)

| Component | Status | Notes |
|-----------|--------|-------|
| process.py | **WORKING** | LLM-based fact extraction |
| analyze.py | **WORKING** | Cross-reference + contradiction detection |
| synthesize.py | **WORKING** | LLM-based report generation |
| verify.py | **WORKING** | LLM-based verification (`detect_contradictions_llm()`) |
| evaluate.py | **WORKING** | Cycle tracking with `cycle_history` |
| Circuit breaker | **INTEGRATED** | In all search providers |
| Proxy rotation | **INTEGRATED** | `ProxyManager` with 3 strategies |
| robots.txt | **INTEGRATED** | `RobotsChecker` with caching |
| Session storage | **INTEGRATED** | `session/storage.py` |
| Export formats | **WORKING** | PDF, DOCX, PPTX, XLSX, MD, JSON |
| Unit Tests | **100% passing** | 800/800 pass |
| Ruff/Mypy | **CLEAN** | No issues |
| GUI | **BUILDS** | SwiftUI macOS app |

**All pipeline components are working. This is a production-ready research assistant.**

---

## SESSION START PROTOCOL

### Step 1: Verify current status
```bash
cd /Users/madsbruusgaard-mouritsen/solid-robot/backend
uv run python -m pytest tests/ -q --tb=no | tail -5
uv run ruff check src/ 2>&1 | tail -3
```

### Step 2: Check git status
```bash
git log --oneline -5
git status
```

### Step 3: Create TodoWrite for tasks
Use TodoWrite tool with specific tasks.

---

## TDD IS OBLIGATORY

### For EACH implementation:

```
1. WRITE TEST FIRST
   - Test should FAIL (red)
   - Run: uv run python -m pytest tests/unit/test_<file>.py -v
   - Confirm FAIL output

2. IMPLEMENT MINIMAL CODE
   - ONLY enough to make test pass
   - No "nice to have" features

3. RUN TEST AGAIN
   - Test should PASS (green)
   - Show output

4. RUN LINTING
   - uv run ruff check src/<file>.py
   - uv run python -m mypy src/<file>.py --ignore-missing-imports

5. COMMIT
   - Max 3 files per commit
```

---

## GIT WORKFLOW

### Commit Message Format:
```bash
git commit -m "type(scope): description

- Detail 1
- Detail 2

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Max 3 files per commit

---

## QUICK REFERENCE COMMANDS

```bash
# Go to backend
cd /Users/madsbruusgaard-mouritsen/solid-robot/backend

# Run tests
uv run python -m pytest tests/ -v

# Run linting
uv run ruff check src/

# Run type check
uv run python -m mypy src/ --ignore-missing-imports

# Start backend
uv run uvicorn src.research_tool.main:app --host 127.0.0.1 --port 8000

# Test health
curl http://localhost:8000/api/health/detailed | python -m json.tool

# Build GUI
cd gui/ResearchTool && swift build
```

---

## KEY SOURCE FILES

| Purpose | File |
|---------|------|
| LLM Router | `src/research_tool/services/llm/router.py` |
| Search Base | `src/research_tool/services/search/provider.py` |
| Fact Extraction | `src/research_tool/agent/nodes/process.py` |
| Analysis | `src/research_tool/agent/nodes/analyze.py` |
| Synthesis | `src/research_tool/agent/nodes/synthesize.py` |
| Verification | `src/research_tool/agent/nodes/verify.py` |
| Evaluation | `src/research_tool/agent/nodes/evaluate.py` |
| Workflow Graph | `src/research_tool/agent/graph.py` |
| Config | `src/research_tool/core/config.py` |
| Proxy Manager | `src/research_tool/services/proxy/manager.py` |
| robots.txt | `src/research_tool/services/compliance/robots.py` |
| Session Storage | `src/research_tool/services/session/storage.py` |
| Research Memory | `src/research_tool/services/memory/research_memory.py` |

---

## PROJECT COMPLETE

All major features are implemented:

- [x] LLM-based pipeline (process, analyze, synthesize, verify, evaluate)
- [x] Circuit breaker pattern in all search providers
- [x] Proxy rotation with health checking
- [x] robots.txt compliance with caching
- [x] Persistent session storage
- [x] Multi-format export (PDF, DOCX, PPTX, XLSX, MD, JSON)
- [x] ResearchMemory with FTS5 search
- [x] SwiftUI macOS GUI with WebSocket
- [x] 800 tests passing

### Future Nice-to-haves
- [ ] Distributed crawling support
- [ ] Multi-user authentication
- [ ] Cloud deployment templates

---

*Last updated: 2025-12-20*
