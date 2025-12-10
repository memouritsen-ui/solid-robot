# CLAUDE CODE INSTRUCTIONS

> ## ⚠️ ADVARSEL: DETTE DOKUMENT ER FORÆLDET
>
> **Brug i stedet:** `CLAUDE.md` og `docs/plans/2025-12-10-professional-research-scraper.md`
>
> Reglerne nedenfor var til original build. Projektet har nu placeholders
> der kræver specifik fix-plan. Se CLAUDE.md for aktuel autoritativ guide.
>
> **Opdateret:** 2025-12-10

---

## Autonomous Operation Rules for Research Tool Build

**CRITICAL**: Read CLAUDE.md first - it supersedes this document.

---

## 1. EXECUTION HIERARCHY

### 1.1 Document Authority (In Order)

1. **META-BUILD-GUIDE-v2.md** — Constitutional authority. NEVER violate.
2. **SPEC.md** — Technical specification. Defines WHAT to build.
3. **BUILD-PLAN.md** — Execution instructions. Defines HOW to build.
4. **TODO.md** — Task checklist. Defines ORDER of work.
5. **Phase docs** — Implementation details for each phase.

### 1.2 Rule Precedence

If instructions conflict:
1. Safety rules (never delete user data, never expose secrets)
2. META guide requirements
3. SPEC technical decisions
4. BUILD-PLAN procedures
5. TODO task order

**When in doubt**: STOP and document the conflict in DECISIONS.md. Do NOT proceed with assumptions.

---

## 2. BEFORE EVERY TASK

### 2.1 Pre-Task Checklist

Before generating ANY code:

```
□ I have read the relevant META guide section
□ I have read the relevant SPEC section
□ I have read the relevant phase document
□ I know which TODO item I'm completing
□ I know what test I need to write FIRST
□ I know how to validate completion
```

### 2.2 Context Loading

At the start of EVERY session, run:

```bash
# Load context
cat docs/META-BUILD-GUIDE-v2.md | head -200  # Key requirements
cat SPEC.md | head -100                       # Architecture
cat TODO.md | grep -A5 "^\- \[ \]" | head -30 # Next tasks
cat DECISIONS.md | tail -20                   # Recent decisions
```

### 2.3 Current State Check

Before coding:

```bash
# Check git status
git status
git branch

# Check test status
cd backend && uv run pytest tests/ -v --tb=short | tail -50

# Check lint status
uv run ruff check . | head -20
uv run mypy src/ | head -20
```

---

## 3. CODING RULES

### 3.1 Test-Driven Development (MANDATORY)

For EVERY implementation:

1. **Write failing test FIRST**
   ```bash
   # Create test file
   # Write test that defines expected behavior
   # Run test - verify it FAILS
   uv run pytest tests/unit/test_new_feature.py -v
   ```

2. **Implement minimum code to pass**
   ```bash
   # Write implementation
   # Run test - verify it PASSES
   uv run pytest tests/unit/test_new_feature.py -v
   ```

3. **Refactor while green**
   ```bash
   # Improve code quality
   # Run ALL tests - verify still passing
   uv run pytest tests/ -v
   ```

### 3.2 Code Standards

Every file must have:
- [ ] Module docstring explaining purpose
- [ ] Type hints on ALL function signatures
- [ ] Docstrings on ALL public functions (Google style)
- [ ] No functions longer than 50 lines
- [ ] No files longer than 500 lines

### 3.3 Import Structure

```python
# Standard library
import os
import sys
from typing import Optional

# Third-party
import fastapi
from pydantic import BaseModel

# Local
from research_tool.core import Settings
from research_tool.models import ResearchState
```

### 3.4 Error Handling

NEVER do this:
```python
try:
    result = do_something()
except:
    pass  # FORBIDDEN - silent failure
```

ALWAYS do this:
```python
try:
    result = do_something()
except SpecificError as e:
    logger.error("operation_failed", error=str(e), context={...})
    raise AppropriateError(f"Failed to do something: {e}") from e
```

### 3.5 Logging

Use structured logging for all significant events:

```python
from research_tool.core import get_logger

logger = get_logger(__name__)

# Good
logger.info("search_completed", source="tavily", results=23, duration_ms=450)

# Bad
print("Search completed with 23 results")  # FORBIDDEN
```

---

## 4. VALIDATION RULES

### 4.1 After EVERY Code Change

Run this sequence:

```bash
cd backend

# 1. Run affected tests
uv run pytest tests/unit/test_affected.py -v

# 2. Run all tests
uv run pytest tests/ -v

# 3. Check linting
uv run ruff check .

# 4. Check types
uv run mypy src/

# If ANY step fails, FIX before proceeding
```

### 4.2 Before EVERY Commit

```bash
# Full validation
./scripts/run_tests.sh

# If all pass, commit
git add .
git commit -m "type(scope): description [TODO.md #X]"
```

### 4.3 Commit Message Format

```
type(scope): description [TODO.md #X]

Types:
- feat: New feature
- fix: Bug fix
- refactor: Code change that doesn't add feature or fix bug
- test: Adding tests
- docs: Documentation
- chore: Maintenance

Examples:
- feat(search): implement Tavily provider [TODO.md #144]
- fix(memory): correct retrieval latency issue [TODO.md #130]
- test(agent): add saturation detection tests [TODO.md #196]
```

---

## 5. BRANCHING RULES

### 5.1 Branch Structure

```
main (protected - never commit directly)
└── develop (integration branch)
    ├── phase-1-foundation
    ├── phase-2-conversational
    ├── phase-3-memory
    ├── phase-4-research
    ├── phase-5-intelligence
    ├── phase-6-export
    └── phase-7-polish
```

### 5.2 Branch Operations

```bash
# Start new phase
git checkout develop
git pull origin develop
git checkout -b phase-X-name

# Work on phase
# ... commits ...

# Complete phase
git checkout develop
git merge phase-X-name
git push origin develop

# Final release
git checkout main
git merge develop
git tag v1.0.0
git push origin main --tags
```

### 5.3 Never Do

- NEVER commit directly to main
- NEVER force push to develop or main
- NEVER merge without passing tests
- NEVER delete phase branches until project complete

---

## 6. ERROR RECOVERY

### 6.1 When a Task Fails

After 3 attempts at same task:

1. **Document the failure**
   ```bash
   # Add to ERROR-LOG.md
   echo "## $(date)" >> ERROR-LOG.md
   echo "Task: TODO.md #X" >> ERROR-LOG.md
   echo "Error: [description]" >> ERROR-LOG.md
   echo "Attempts: 3" >> ERROR-LOG.md
   echo "Status: BLOCKED" >> ERROR-LOG.md
   ```

2. **Check ERROR-HANDLING.md** for recovery procedure

3. **If no procedure exists**, STOP and wait for user

### 6.2 When Tests Fail

```bash
# Get detailed output
uv run pytest tests/path/to/test.py -v --tb=long

# Check if it's a flaky test
uv run pytest tests/path/to/test.py -v --count=3

# If consistently failing, debug:
# 1. Read the test carefully
# 2. Read the implementation
# 3. Check META guide for correct behavior
# 4. Fix implementation (not test, unless test is wrong)
```

### 6.3 When Lint/Type Check Fails

```bash
# Ruff - often auto-fixable
uv run ruff check . --fix

# Mypy - requires manual fix
# Read error carefully
# Add type hints as needed
# Use typing module (Optional, Union, etc.)
```

### 6.4 When Build Fails (SwiftUI)

1. Check Xcode error messages
2. Verify all files are in correct locations
3. Verify imports match file structure
4. Clean build folder (Cmd+Shift+K)
5. Rebuild

---

## 7. ANTI-PATTERN PREVENTION

### 7.1 Before Implementing Query Clarification

Re-read:
- META guide Section 1.1 Criterion #1 and #5
- META guide Section 5.1 Anti-Patterns #1 and #2
- META guide Section 7.3 Decision Tree

**Rule**: If you can proceed with reasonable interpretation, DO NOT ask for clarification.

### 7.2 Before Implementing Search

Re-read:
- META guide Section 3.5 (Search Tool Configs)
- META guide Section 5.2 Anti-Patterns #3, #4, #5
- META guide Section 7.2 Decision Tree

**Rule**: Always use saturation metrics to decide when to stop.

### 7.3 Before Implementing Memory

Re-read:
- META guide Section 4.1.3 (Memory Schema)
- META guide Section 5.4 Anti-Patterns #8 and #9

**Rule**: Always read memory BEFORE planning, always write memory AFTER research.

### 7.4 Before Implementing Model Selection

Re-read:
- META guide Section 3.3 (LiteLLM Router)
- META guide Section 5.5 Anti-Pattern #10
- META guide Section 7.1 Decision Tree

**Rule**: LOCAL_ONLY is a HARD constraint. NEVER violate.

### 7.5 Before Implementing Output

Re-read:
- META guide Section 5.6 Anti-Patterns #11 and #12

**Rule**: Always include what wasn't found and why you stopped.

---

## 8. DECISION LOGGING

### 8.1 When to Log

Log in DECISIONS.md when:
- Making a choice not explicitly covered by docs
- Encountering ambiguity
- Deviating from plan (with justification)
- Discovering new information that affects build

### 8.2 Decision Format

```markdown
## [Date] - [Topic]

**Context**: [What situation required a decision]

**Options Considered**:
1. [Option A] - [Pros/Cons]
2. [Option B] - [Pros/Cons]

**Decision**: [What was decided]

**Rationale**: [Why this decision]

**References**: [SPEC section, META guide section, etc.]
```

---

## 9. PARALLEL EXECUTION (If Using Multiple Terminals)

### 9.1 Allowed Parallel Work

- Different phases on different branches
- Tests in one terminal, implementation in another
- Backend and GUI simultaneously (different directories)

### 9.2 NOT Allowed Parallel Work

- Same file in multiple terminals
- Same branch in multiple terminals
- Conflicting changes to shared code

### 9.3 Synchronization

Before starting parallel work:
```bash
git pull origin develop
```

Before merging:
```bash
git fetch origin
git merge origin/develop
# Resolve conflicts per SPEC
```

---

## 10. COMPLETION CRITERIA

### 10.1 Task Complete When

- [ ] Test written and passing
- [ ] Implementation matches SPEC
- [ ] No lint warnings
- [ ] No type errors
- [ ] Docstrings complete
- [ ] Committed with proper message
- [ ] TODO.md item marked [x]

### 10.2 Phase Complete When

- [ ] All phase tasks in TODO.md marked [x]
- [ ] Phase validation gate passed (META guide Section 6.3)
- [ ] No failing tests
- [ ] Merged to develop
- [ ] MERGELOG.md updated

### 10.3 Project Complete When

- [ ] All 307 tasks complete
- [ ] All 8 success criteria verified
- [ ] All anti-patterns verified NOT present
- [ ] All performance benchmarks met
- [ ] Merged to main
- [ ] Tagged v1.0.0

---

## 11. EMERGENCY PROCEDURES

### 11.1 If Everything Breaks

```bash
# Save current state
git stash

# Return to last known good state
git checkout develop
git pull origin develop

# Assess damage
git stash show -p

# Either apply stash and fix, or discard
git stash drop  # If unsalvageable
```

### 11.2 If Need User Help

1. Document situation in DECISIONS.md
2. Include:
   - What you were trying to do
   - What went wrong
   - What you've tried
   - What you need to proceed
3. STOP execution
4. Wait for user response

### 11.3 If Spec is Wrong

NEVER assume the spec is wrong. If you believe there's an error:

1. Document your reasoning in DECISIONS.md
2. Reference META guide to support your case
3. STOP and wait for user confirmation
4. Do NOT proceed with "corrected" implementation

---

## 12. FINAL REMINDERS

1. **Read docs before coding** — Every time
2. **Test first** — Write the test before the implementation
3. **Validate always** — Run tests after every change
4. **Commit often** — Small, atomic commits
5. **Log decisions** — When in doubt, write it down
6. **Stop when stuck** — 3 attempts max, then document and wait
7. **Never assume** — When unclear, check docs or ask
8. **Follow the plan** — The plan exists for a reason

---

*END OF CLAUDE CODE INSTRUCTIONS*
