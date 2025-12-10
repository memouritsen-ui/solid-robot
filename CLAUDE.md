# CLAUDE.md - SOLID-ROBOT Professional Research Scraper

## KRITISK: LÆS DETTE FØR DU GØR NOGET

**Du er ved at arbejde på et projekt hvor PLACEHOLDERS er blevet præsenteret som færdig kode.**

### FAKTA OM DETTE PROJEKT (VERIFICERET 2025-12-10):

| Komponent | Dokumentation siger | FAKTISK STATUS |
|-----------|---------------------|----------------|
| process.py | "Complete" | **PLACEHOLDER** - genererer FAKE facts |
| analyze.py | "Complete" | **TOM SHELL** - gør ingenting |
| synthesize.py | "Complete" | **PLACEHOLDER** - ingen LLM syntese |
| Circuit breaker | "Integrated" | **IKKE INTEGRERET** i providers |
| Tests | "683+ passing" | Tester placeholders, ikke reel funktionalitet |

---

## OBLIGATORISK: SESSION START PROTOKOL

**HVER SESSION STARTER MED DISSE TRIN:**

### Step 1: Læs implementeringsplanen
```bash
cat /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/docs/plans/2025-12-10-professional-research-scraper.md
```

### Step 2: Verificer nuværende status
```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/ -q --tb=no | tail -5
uv run ruff check src/ 2>&1 | tail -3
```

### Step 3: Find hvor du er i planen
Tjek git log for seneste commits og match med plan tasks:
```bash
git log --oneline -10
```

### Step 4: Opret TodoWrite for dagens opgaver
Brug TodoWrite tool med præcise tasks fra planen.

---

## FORBUDTE HANDLINGER

### DU MÅ ALDRIG:

1. **Improvisere løsninger** - Følg planen PRÆCIST
2. **Skippe tests** - TDD er obligatorisk (test FØRST, så kode)
3. **Ændre mere end 3 filer per commit** - Split større ændringer
4. **Sige "det virker"** uden at vise test output
5. **Tilføje features** der ikke er i planen
6. **"Forbedre" eksisterende kode** medmindre det er en task
7. **Refaktorere** uden explicit task i planen

### HVIS DU OVERTRÆDER DISSE REGLER:
Brugeren vil sige **"AIRPORT"** og du skal:
1. STOP med det samme
2. Erkend hvad du gjorde forkert
3. Gå tilbage til planen
4. Start forfra med korrekt fremgangsmåde

---

## TDD ER OBLIGATORISK

### For HVER implementation:

```
1. SKRIV TEST FØRST
   - Test skal FEJLE (rød)
   - Kør: uv run python -m pytest tests/unit/test_<file>.py -v
   - Bekræft FAIL output

2. IMPLEMENTER MINIMAL KODE
   - KUN nok til at testen passer
   - Ingen "nice to have" features
   - Ingen "mens jeg er i gang" tilføjelser

3. KØR TEST IGEN
   - Test skal PASSE (grøn)
   - Vis output

4. KØR LINTING
   - uv run ruff check src/<file>.py
   - uv run python -m mypy src/<file>.py --ignore-missing-imports

5. COMMIT
   - Max 3 filer per commit
   - Brug commit message fra planen
```

---

## TASK STRUKTUR FRA PLANEN

Hver task i planen har dette format:

```
## Task X.Y: [Navn]

**Problem:** Hvad der er galt
**Files:** Hvilke filer der skal ændres

**Step 1:** Første handling
**Step 2:** Næste handling
...
**Step N:** Commit
```

### DU SKAL:
- Følge HVERT step i rækkefølge
- IKKE springe steps over
- IKKE tilføje ekstra steps
- IKKE kombinere steps

---

## VERIFICERING EFTER HVER TASK

```bash
# Efter HVER task, kør:
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/ -v --tb=short -q | tail -10
uv run ruff check src/
uv run python -m mypy src/ --ignore-missing-imports | tail -3
```

**VIS OUTPUT TIL BRUGER** - "Tests pass" uden output = VIOLATION

---

## GIT WORKFLOW

### Commit Message Format (fra planen):
```bash
git commit -m "type(scope): description

- Detail 1
- Detail 2"
```

### Max 3 filer per commit:
| Filer | Handling |
|-------|----------|
| 1-3   | OK - commit |
| 4+    | SPLIT - lav flere commits |

### Aldrig commit uden test:
```bash
# FORKERT:
git add .
git commit -m "fix stuff"

# KORREKT:
uv run python -m pytest tests/unit/test_<file>.py -v  # Vis output
uv run ruff check src/<file>.py  # Vis output
git add <specific files>
git commit -m "feat(process): implement LLM fact extraction"
```

---

## HUSK: DETTE ER PRIORITETSORDENEN

1. **Planen** i `/docs/plans/2025-12-10-professional-research-scraper.md`
2. **Denne CLAUDE.md**
3. Brugerens instruktioner (hvis de ikke konflikter med 1 og 2)

---

## FASE OVERSIGT

| Fase | Indhold | Status |
|------|---------|--------|
| 1    | Foundation Fix (path, config, health) | TODO |
| 2    | Search Provider Integration | TODO |
| 3    | Pipeline Nodes (process, analyze, synthesize) | TODO |
| 4    | Production Hardening (E2E tests) | TODO |

---

## QUICK REFERENCE: Dagens Kommandoer

```bash
# Gå til backend
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend

# Kør tests
uv run python -m pytest tests/ -v

# Kør linting
uv run ruff check src/

# Kør type check
uv run python -m mypy src/ --ignore-missing-imports

# Start backend
uv run uvicorn src.research_tool.main:app --host 127.0.0.1 --port 8000

# Test health
curl http://localhost:8000/api/health/detailed | python -m json.tool
```

---

## NÅR DU ER FÆRDIG MED EN SESSION

1. Kør alle verificeringskommandoer
2. Commit alle ændringer
3. Opdater denne fil med status
4. Giv handoff til næste session:

```
## SESSION HANDOFF

### Completed:
- [x] Task X.Y
- [x] Task X.Z

### Current State:
- Tests: X passed
- Lint: Clean
- Types: Clean

### Next Session Should:
1. Start med Task X.W
2. Læs planen fra linje Y
```

---

## PLAN DOKUMENTER (LÆS I RÆKKEFØLGE)

| # | Dokument | Indhold |
|---|----------|---------|
| 1 | `docs/plans/DOCUMENT_STATUS.md` | Hvilke docs er pålidelige vs vildledende |
| 2 | `docs/plans/2025-12-10-professional-research-scraper.md` | **HOVEDPLAN** - følg denne |
| 3 | `docs/plans/SUPPLEMENT-provider-code.md` | Komplet kode for ALLE providers |
| 4 | `docs/plans/SUPPLEMENT-llm-and-tests.md` | LLMRouter interface + test håndtering |
| 5 | `docs/plans/SUPPLEMENT-git-and-errors.md` | Git strategi + error recovery |

---

## START-SEKVENS FOR NY SESSION

```bash
# 1. Gå til projekt
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT

# 2. Verificer branch
git branch
# Skal vise: fix/professional-scraper

# 3. Læs hvor vi er
git log --oneline -5

# 4. Find næste task
# Match seneste commit med tasks i hovedplanen

# 5. Læs task fra plan
cat docs/plans/2025-12-10-professional-research-scraper.md | grep -A 50 "Task X.Y"

# 6. Udfør PRÆCIS hvad der står
```

---

*Sidst opdateret: 2025-12-10*
*Plan version: 2025-12-10-professional-research-scraper.md*
*Supplementer: 3 dokumenter*
