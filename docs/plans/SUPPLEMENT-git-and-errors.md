# SUPPLEMENT: Git Strategi & Fejlhåndtering

> **KRITISK:** Dette dokument definerer git workflow og error recovery procedures.

---

## DEL 1: GIT BRANCH STRATEGI

### Nuværende Status

```
main ─────────────────────────────────────── (initial)
  │
  └── develop ─────────────────────────────── (current, placeholders)
```

### Ny Strategi

```
main ─────────────────────────────────────── (stable, DO NOT TOUCH)
  │
  └── develop ─────────────────────────────── (placeholders)
        │
        └── fix/professional-scraper ──────── (NY BRANCH FOR PLANEN)
```

### Hvorfor Ny Branch?

1. **Beskyt develop** - Hvis noget går galt, kan vi slette branchen
2. **Atomic changes** - Hele planen kan merges som én PR
3. **Review mulig** - Kan gennemgås før merge

---

## DEL 2: INITIAL GIT SETUP

### Step 1: Verificer Clean State

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
git status

# Forventet: "nothing to commit, working tree clean"
# Hvis IKKE clean: commit eller stash ændringer først
```

### Step 2: Opret Fix Branch

```bash
git checkout develop
git pull origin develop 2>/dev/null || true  # OK hvis no remote
git checkout -b fix/professional-scraper
```

### Step 3: Commit Planen Først

```bash
git add docs/plans/
git add CLAUDE.md
git commit -m "docs: add professional scraper implementation plan

- Add comprehensive 4-phase implementation plan
- Add document status audit
- Add provider code supplement
- Add LLM and test handling supplement
- Add git strategy and error recovery
- Update CLAUDE.md with enforcement rules"
```

---

## DEL 3: COMMIT STRATEGI FOR PLANEN

### Commit Grupper

| Gruppe | Tasks | Commit Message |
|--------|-------|----------------|
| 1 | 1.1 | `fix(gui): robust backend path resolution` |
| 2 | 1.2-1.3 | `feat(config): validation and status reporting` |
| 3 | 1.4-1.5 | `feat(health): deep health check and startup tests` |
| 4 | 2.1 | `refactor(providers): integrate circuit breaker in base class` |
| 5 | 2.2-2.3 | `refactor(providers): update all providers to use _do_search` |
| 6 | 3.1 | `feat(process): implement LLM-based fact extraction` |
| 7 | 3.2 | `feat(analyze): implement cross-reference detection` |
| 8 | 3.3 | `feat(synthesize): implement LLM report generation` |
| 9 | 4.1-4.2 | `test(e2e): add end-to-end test suite` |

### Mellem Commits

Efter HVER commit:
```bash
# Verificer
uv run python -m pytest tests/unit/ -v --tb=short -q | tail -10
uv run ruff check src/

# Hvis OK, fortsæt til næste task
# Hvis FEJL, se error recovery nedenfor
```

---

## DEL 4: ERROR RECOVERY PROCEDURES

### Scenario 1: Test Fejler Efter Kode-ændring

**Symptom:** `pytest` viser FAILED tests

**Recovery:**

```bash
# 1. Se præcis hvad der fejlede
uv run python -m pytest tests/unit/<test_file>.py -v --tb=long

# 2. Tjek at ændringen matcher planen PRÆCIST
cat src/research_tool/agent/nodes/<file>.py | head -50

# 3. Sammenlign med planen
cat docs/plans/2025-12-10-professional-research-scraper.md | grep -A 100 "Step 4:"

# 4. Ret PRÆCIS til hvad planen siger - INGEN improvisation

# 5. Kør test igen
uv run python -m pytest tests/unit/<test_file>.py -v
```

### Scenario 2: Import Fejl

**Symptom:** `ModuleNotFoundError` eller `ImportError`

**Recovery:**

```bash
# 1. Verificer fil eksisterer
ls -la src/research_tool/<path>/

# 2. Tjek __init__.py exports
cat src/research_tool/<path>/__init__.py

# 3. Tilføj manglende import til __init__.py
# Følg eksisterende mønster i filen
```

### Scenario 3: Type Fejl (mypy)

**Symptom:** `mypy` viser errors

**Recovery:**

```bash
# 1. Se præcis error
uv run python -m mypy src/<file>.py --ignore-missing-imports

# 2. Typiske fixes:
#    - Manglende return type: Tilføj -> Type
#    - None check: Tilføj `if x is not None:`
#    - Optional: Brug `Type | None`

# 3. Kør mypy igen
```

### Scenario 4: Lint Fejl (ruff)

**Symptom:** `ruff check` viser errors

**Recovery:**

```bash
# 1. Autofix hvis muligt
uv run ruff check src/<file>.py --fix

# 2. Hvis ikke autofix:
uv run ruff check src/<file>.py
# Læs error message og ret manuelt

# 3. Kør igen
uv run ruff check src/<file>.py
```

### Scenario 5: Git Conflict

**Symptom:** `git merge` eller `git rebase` conflict

**Recovery:**

```bash
# 1. ALDRIG force push eller --hard reset
# 2. Se conflicts
git status

# 3. Åbn conflicted files og vælg korrekt version
# <<<<<<< HEAD
# Din kode
# =======
# Anden kode
# >>>>>>> branch

# 4. Behold din kode (fra fix/professional-scraper)
# 5. git add <file>
# 6. git commit
```

### Scenario 6: LLM Test Fejler (API Key)

**Symptom:** Test fejler med `ModelUnavailableError`

**Recovery:**

```bash
# 1. Tjek API key er sat
grep ANTHROPIC_API_KEY backend/.env

# 2. Hvis tom, tilføj din key
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" >> backend/.env

# 3. For lokale tests, start Ollama
ollama serve &
ollama pull llama3.1:8b

# 4. Kør tests igen med --slow flag
uv run python -m pytest tests/integration/test_llm_router_live.py -v -m slow
```

### Scenario 7: Swift Build Fejler

**Symptom:** Xcode build error

**Recovery:**

```bash
# 1. Clean build folder
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/gui/ResearchTool
rm -rf .build/

# 2. Resolve packages
swift package resolve

# 3. Build igen
swift build -c release

# 4. Hvis stadig fejl, tjek Swift syntax i ændrede filer
```

---

## DEL 5: ABORT PROCEDURE

### Hvis Alt Går Galt

Hvis du er kørt helt fast og ikke kan løse problemet:

```bash
# 1. GEM nuværende state som patch
git diff > ~/emergency-patch-$(date +%Y%m%d-%H%M%S).patch

# 2. Log hvad du gjorde
echo "Stopped at task X.Y because: <reason>" > ~/abort-log.txt

# 3. Gå tilbage til clean state
git checkout develop
git branch -D fix/professional-scraper  # Slet problematisk branch

# 4. Start forfra
git checkout -b fix/professional-scraper

# 5. Begynd fra task 1.1 igen
```

---

## DEL 6: FINAL MERGE PROCEDURE

### Når ALLE Tasks Er Færdige

```bash
# 1. Verificer ALLE tests passer
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/ -v
uv run ruff check src/ tests/
uv run python -m mypy src/ --ignore-missing-imports

# 2. Verificer GUI builder
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/gui/ResearchTool
swift build -c release

# 3. Merge til develop
git checkout develop
git merge fix/professional-scraper --no-ff -m "feat: complete professional scraper implementation

Phases completed:
- Phase 1: Foundation Fix
- Phase 2: Search Provider Integration
- Phase 3: Research Pipeline Nodes
- Phase 4: Production Hardening

Tests: All passing
Lint: Clean
Types: Clean"

# 4. Tag version
git tag -a v1.1.0 -m "Professional scraper release"

# 5. VALGFRIT: Merge til main
git checkout main
git merge develop --no-ff -m "release: v1.1.0 professional scraper"
```

---

*Dette dokument sikrer at fejl kan håndteres uden panik.*
