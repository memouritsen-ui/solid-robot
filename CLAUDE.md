# CLAUDE.md - SOLID-ROBOT Professional Research Scraper

## CURRENT STATUS (Updated 2025-12-17)

| Component | Status | Notes |
|-----------|--------|-------|
| process.py | **WORKING** | LLM-based fact extraction |
| analyze.py | **WORKING** | Cross-reference + contradiction detection |
| synthesize.py | **WORKING** | LLM-based report generation |
| Circuit breaker | **INTEGRATED** | In all search providers |
| Unit Tests | **100% passing** | 617/617 pass |
| Ruff/Mypy | **CLEAN** | No issues |

**All core pipeline components are working. Tests validated against real LLM-based implementation.**

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
| Workflow Graph | `src/research_tool/agent/graph.py` |
| Config | `src/research_tool/core/config.py` |

---

## REMAINING WORK

### Priority 1: Complete placeholders
- `verify.py` - Upgrade from regex to LLM-based verification
- `evaluate.py` - Track saturation across cycles properly

### Priority 2: Professional features
- Proxy rotation
- robots.txt compliance
- Persistent session storage

---

*Last updated: 2025-12-17*
