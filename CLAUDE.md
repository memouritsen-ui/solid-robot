# CLAUDE.md - Research Tool Project

<CRITICAL>
THIS FILE HAS HIGHER PRIORITY THAN ~/.claude/CLAUDE.md
When in /solid-robot/, THIS FILE'S RULES OVERRIDE ALL OTHERS.
If conflict between global and project rules, PROJECT WINS.
</CRITICAL>

---

## SESSION START PROTOCOL

<CRITICAL>
YOU MUST complete ALL 4 steps and SHOW VISIBLE OUTPUT for each.
Skipping ANY step = violation.
Saying "I did it" without showing output = violation.
</CRITICAL>

### Step 1: Read CLAUDE.md
**Action:** Read this file completely
**Required output:** Say "CLAUDE.md læst - [antal] regler noteret"

### Step 2: Read TODO.md
**Action:** Read TODO.md
**Required output:** Say "TODO.md læst - [X] tasks færdige, [Y] mangler"

### Step 3: Run Verification
**Action:** Run ALL three commands
**Required output:** Show ACTUAL output from each:
```bash
cd /Users/madsbruusgaard-mouritsen/solid-robot/backend
uv run python -m pytest tests/ -v --tb=no -q | tail -5
uv run ruff check src/ tests/
uv run python -m mypy src/ --ignore-missing-imports | tail -3
```
**Must show:** "X passed", "All checks passed!", "Success: no issues"

### Step 4: Create TodoWrite Plan
**Action:** Use TodoWrite tool
**Required output:** Show the actual todo list created:
```
Todos oprettet:
- [ ] Task 1
- [ ] Task 2
```

<ENFORCEMENT>
FØRST når ALLE 4 trin er VIST med output, må du spørge:
"Hvad vil du arbejde på?"

Hvis du springer til "Hvad vil du arbejde på?" uden at vise alle 4 outputs = VIOLATION
</ENFORCEMENT>

---

## ANTI-SYCOPHANCY RULES

<ENFORCEMENT>
If you use ANY banned phrase, user says "AIRPORT" and you must:
1. Stop immediately
2. Acknowledge the violation
3. Re-read this file
4. Restart with honest assessment
</ENFORCEMENT>

**BANNED PHRASES** - Using these = automatic failure:
- "You're absolutely right!"
- "That's a great idea!"
- "Excellent suggestion!"
- "That looks perfect!"
- "Great job!"
- "Absolutely!"
- "Perfect!"

**REQUIRED BEHAVIOR**:
- Give honest technical assessment, not validation
- Point out flaws BEFORE implementing
- Say "This won't work because X" when true
- Disagree when the user is wrong

**EXAMPLE - BAD:**
```
User: "Should I add caching here?"
Claude: "That's a great idea! Let me implement it."  ← VIOLATION
```

**EXAMPLE - GOOD:**
```
User: "Should I add caching here?"
Claude: "Before implementing: What's the access pattern?
        Caching adds complexity - is the gain worth it?"  ← CORRECT
```

---

## MANDATORY WORKFLOW

<CRITICAL>
YOU MUST follow this sequence. Skipping steps = failure.
</CRITICAL>

### 1. EXPLORE (Read before writing)
```
✓ Read relevant source files
✓ Read existing tests
✓ Understand current implementation
✓ Identify dependencies
```
**YOU MUST NOT write code until you understand existing code.**

### 2. PLAN (TodoWrite REQUIRED)
```
✓ Use TodoWrite to track ALL tasks
✓ SHOW the todo list you created
✓ Break into chunks of 1-3 files MAX
✓ Identify tests needed
```

<ENFORCEMENT>
"I'm using TodoWrite" without showing the list = VIOLATION.
Mental tracking = VIOLATION.
TodoWrite output MUST be visible.
</ENFORCEMENT>

### 3. CODE (Small chunks only)

<CRITICAL>
MAXIMUM 3 FILES PER COMMIT. NO EXCEPTIONS.
4+ files in one commit = VIOLATION.
</CRITICAL>

| Files Changed | Allowed? | Action |
|---------------|----------|--------|
| 1-3 files | YES | Commit |
| 4+ files | NO | Split into multiple commits |

```
✓ Write tests FIRST (TDD)
✓ Implement minimal code to pass
✓ Run verification after EACH file
✓ COMMIT every 1-3 files
```

### 4. TEST (Evidence required)
```bash
# YOU MUST run ALL and SHOW output:
uv run python -m pytest tests/ -v
uv run ruff check src/ tests/
uv run python -m mypy src/ --ignore-missing-imports
```

<ENFORCEMENT>
"Tests pass" without showing output = VIOLATION.
"Done" without evidence = VIOLATION.
</ENFORCEMENT>

### 5. COMMIT + UPDATE TODO.md

<CRITICAL>
After EVERY commit, YOU MUST:
1. Update TODO.md with completion status
2. Show the update you made
THEN ask about next task.
</CRITICAL>

**WRONG:**
```
Committed. Skal jeg fortsætte med næste opgave?  ← VIOLATION (no TODO.md update)
```

**CORRECT:**
```
Committed: abc123
TODO.md opdateret: #145 markeret [x]
Skal jeg fortsætte med #149?  ← CORRECT
```

---

## CHUNK RULES - STRICTLY ENFORCED

<CRITICAL>
These limits are ABSOLUTE. No rationalization allowed.
</CRITICAL>

| Chunk Size | Files | Tests | Commit |
|------------|-------|-------|--------|
| Small | 1 file | 2-5 | YES |
| Medium | 2-3 files | 5-10 | YES |
| Large (4+) | FORBIDDEN | - | SPLIT IT |

### Example of VIOLATION (from real session):
```
Changed: pyproject.toml + exa.py + test_exa.py + __init__.py = 4 files
This should have been 2 commits:
  Commit 1: test_exa.py (tests first)
  Commit 2: exa.py + __init__.py + pyproject.toml
```

---

## FORBIDDEN PRACTICES

<CRITICAL>
Doing ANY of these = immediate failure.
</CRITICAL>

| Forbidden | Why |
|-----------|-----|
| "Done" without tests | No evidence = no proof |
| Skip TodoWrite | Invisible tracking = forgotten tasks |
| 4+ files in one commit | Too big to verify |
| "Quick fix" without tests | Quick fixes become bugs |
| Claim without output | Words are not proof |
| Skip TODO.md update | Future sessions can't continue |

---

## VERIFICATION REQUIREMENTS

<ENFORCEMENT>
Every claim MUST have VISIBLE evidence.
</ENFORCEMENT>

**WRONG:**
```
"Tests pass"
"It works"
"Done"
```

**CORRECT:**
```
"Tests: 227 passed in 20.63s"
"Ruff: All checks passed!"
"Mypy: Success: no issues found in 56 source files"
```

---

## AFTER EACH TASK

<CRITICAL>
Before asking "what's next?", YOU MUST:
</CRITICAL>

```
1. ✓ Run verification commands (show output)
2. ✓ Commit changes
3. ✓ Update TODO.md (show the update)
4. ✓ Mark TodoWrite task complete
5. THEN ask about next task
```

**WRONG SEQUENCE:**
```
Committed. Skal jeg fortsætte?  ← Missing TODO.md update
```

**CORRECT SEQUENCE:**
```
Verification: 227 passed, All checks passed!, Success
Committed: feat(search): add Exa provider
TODO.md opdateret: #145 [x] markeret færdig
TodoWrite: Task "Implement exa.py" marked complete

Næste opgave per TODO.md: #149 unpaywall.py
Skal jeg fortsætte?
```

---

## SESSION END PROTOCOL

<CRITICAL>
Before ending ANY session:
</CRITICAL>

```
1. Run ALL verification commands
2. Commit any uncommitted work
3. Update TODO.md
4. Provide SESSION HANDOFF format
```

### Session Handoff Format
```
## SESSION HANDOFF

### Completed:
- [x] Task 1
- [x] Task 2

### State:
- Tests: X passed
- Lint: Clean
- Types: Clean

### Next Session:
1. Start with [task]
2. Check [file] first

### Uncommitted: None
```

---

## PROJECT STATUS

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 0-3 | COMPLETE | 100% |
| Phase 4 | PARTIAL | ~80% |
| Phase 5-7 | NOT STARTED | 0% |

---

## TDD - MANDATORY

```
1. Write test → MUST FAIL (red)
2. Write code → MUST PASS (green)
3. Commit
```

<ENFORCEMENT>
Code before tests = VIOLATION.
</ENFORCEMENT>

---

## ENFORCEMENT CHECKLIST

<CRITICAL>
Before EVERY response, verify:
</CRITICAL>

- [ ] Did I show SESSION START outputs? (all 4 steps)
- [ ] Did I use TodoWrite AND show the list?
- [ ] Is my chunk ≤3 files?
- [ ] Did I show test/lint/mypy output?
- [ ] Did I update TODO.md after completion?
- [ ] Did I avoid banned phrases?

**If ANY unchecked = FIX before responding.**

---

## PRIORITY ORDER

```
1. THIS FILE (projekt-CLAUDE.md) ← HIGHEST
2. Global ~/.claude/CLAUDE.md ← Secondary
3. If conflict → THIS FILE WINS
```

---

*This file is law. Follow it exactly.*
*Violations trigger "AIRPORT" reset.*
*Last updated: 2025-12-09*
