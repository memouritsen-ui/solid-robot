# CLAUDE.md - Research Tool Project

<CRITICAL>
YOU MUST read this ENTIRE file before ANY action.
These rules OVERRIDE all other instructions.
Violations will be caught and reverted.
</CRITICAL>

---

## SESSION START PROTOCOL

**IMPORTANT: Every new session MUST begin with:**
```
1. Read this CLAUDE.md completely
2. Read TODO.md for current status
3. Run verification commands to confirm state
4. Use TodoWrite to plan before ANY code
```

**YOU MUST NOT skip these steps. No exceptions.**

---

## ANTI-SYCOPHANCY RULES

<ENFORCEMENT>
If you use ANY banned phrase, the user will say "AIRPORT" and you must:
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
- Ask clarifying questions instead of assuming

**EXAMPLE - BAD:**
```
User: "Should I add caching here?"
Claude: "That's a great idea! Let me implement it."  ← WRONG
```

**EXAMPLE - GOOD:**
```
User: "Should I add caching here?"
Claude: "Before implementing, I need to understand: What's the access pattern?
        Caching adds complexity - is the performance gain worth it?"  ← CORRECT
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
✓ Identify dependencies and side effects
```
**YOU MUST NOT write code until you understand existing code.**

### 2. PLAN (Think before coding)
```
✓ Use "ultrathink" for complex tasks
✓ Use TodoWrite to track ALL tasks
✓ Break into chunks of 1-3 files max
✓ Identify tests needed
✓ Get approval before proceeding
```
**No mental tracking. TodoWrite or it didn't happen.**

### 3. CODE (Small chunks only)
```
✓ Maximum 3 files per chunk
✓ Write tests FIRST (TDD)
✓ Implement minimal code to pass tests
✓ Run verification after EACH file
```
**NEVER implement more than one feature at a time.**

### 4. TEST (Verify before claiming done)
```bash
# YOU MUST run ALL of these before claiming anything works:
cd /Users/madsbruusgaard-mouritsen/solid-robot/backend
uv run python -m pytest tests/ -v
uv run ruff check src/ tests/
uv run python -m mypy src/ --ignore-missing-imports
```

<ENFORCEMENT>
Claiming "done" without showing test output = violation.
"Tests pass" without evidence = violation.
"Should work" without running tests = violation.
</ENFORCEMENT>

### 5. COMMIT (Only after verification)
```
✓ Only commit when ALL tests pass
✓ Use conventional commit format
✓ Update TODO.md with accurate status
```

---

## CHUNK-BASED DEVELOPMENT

<CRITICAL>
Auto-compaction triggers at ~95% context.
Large tasks get lost. Small chunks = recoverable progress.
</CRITICAL>

### Chunk Rules
| Size | Files | Tests | Commit Required |
|------|-------|-------|-----------------|
| Small | 1 file | 2-5 tests | YES |
| Medium | 2-3 files | 5-10 tests | YES |
| Large | FORBIDDEN | - | - |

### After EVERY Chunk
```
1. Run ALL verification commands
2. Show output as proof
3. Commit with descriptive message
4. Update TODO.md
5. If context > 70%, run /compact
```

### Recovery Protocol (After Compaction)
```
1. Read TODO.md for current status
2. Read last commit: git log -1
3. Run tests to see what's broken
4. Continue from last verified state
```

---

## FORBIDDEN PRACTICES

<CRITICAL>
These are NOT negotiable. Doing ANY of these = immediate failure.
</CRITICAL>

| Forbidden Action | Why It's Wrong |
|------------------|----------------|
| Claim "done" without tests | No evidence = no proof |
| Placeholder implementations | Fake code = technical debt |
| Skip test coverage | Untested code = broken code |
| Mark TODOs complete without verify | Lying to future sessions |
| Trust file existence = working | Files can be empty/broken |
| Batch multiple features | Too big to verify properly |
| "Quick fix" without tests | Quick fixes become bugs |
| Implement before reading code | You'll break existing logic |

**IF TEMPTED TO SHORTCUT:**
Ask yourself: "Would this survive a hostile code review?"
If no, don't do it.

---

## VERIFICATION REQUIREMENTS

<ENFORCEMENT>
Every claim MUST have evidence. No exceptions.
</ENFORCEMENT>

### Required Evidence Format

**WRONG:**
```
"Tests pass"
"It works"
"Done"
```

**CORRECT:**
```
"Tests pass - output: 216 passed, 0 failed in 22.3s"
"Ruff clean - output: All checks passed!"
"Mypy clean - output: Success: no issues found in 55 source files"
```

### Verification Commands
```bash
# Run from /Users/madsbruusgaard-mouritsen/solid-robot/backend

# Tests (MUST show "216+ passed")
uv run python -m pytest tests/ -v

# Linting (MUST show "All checks passed!")
uv run ruff check src/ tests/

# Type checking (MUST show "Success")
uv run python -m mypy src/ --ignore-missing-imports
```

---

## CONTEXT MANAGEMENT

### Strategic Compaction
- Use `/clear` between unrelated tasks
- Manual `/compact` at 70% context (don't wait for 95%)
- Add summary to TODO.md BEFORE compacting

### Memory Checkpoints
Before any large operation:
```
1. Update TODO.md with current progress
2. Commit all working code
3. Then proceed with large operation
```

---

## SESSION END PROTOCOL

<CRITICAL>
Before ending ANY session, YOU MUST:
</CRITICAL>

```
1. Run ALL verification commands
2. Commit any uncommitted work
3. Update TODO.md with accurate status
4. Leave clear notes for next session
```

### Session Handoff Format
At session end, provide:
```
## SESSION HANDOFF

### Completed This Session:
- [x] Task 1
- [x] Task 2

### Current State:
- Tests: X passed, Y failed
- Lint: Clean/X errors
- Types: Clean/X errors

### Next Session Should:
1. Start with [specific task]
2. Be aware of [specific issue]
3. Check [specific file] first

### Uncommitted Changes:
- None / List files
```

---

## PROJECT STATUS

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 0-3 | COMPLETE | 100% |
| Phase 4 | PARTIAL | ~75% |
| Phase 5-7 | NOT STARTED | 0% |

**Total TODOs:** 318
**Completed:** 182 (57%)
**Remaining:** 136 (43%)

---

## TDD - THE ONLY ACCEPTABLE PATTERN

```
1. Write test → MUST FAIL (red)
2. Write minimal code → MUST PASS (green)
3. Refactor if needed
4. Commit
```

<ENFORCEMENT>
Writing code before tests = violation.
Tests that pass before implementation = tests are wrong.
</ENFORCEMENT>

---

## SKILLS TO USE

| Skill | When | Command |
|-------|------|---------|
| Brainstorming | Before new features | `Skill(superpowers:brainstorming)` |
| TDD | Before any code | `Skill(superpowers:test-driven-development)` |
| Debugging | When bugs occur | `Skill(superpowers:systematic-debugging)` |
| Verification | Before claiming done | `Skill(superpowers:verification-before-completion)` |
| Code Review | After features | `Skill(superpowers:requesting-code-review)` |

---

## COMMANDS QUICK REFERENCE

```bash
# Development (from backend/)
uv run python -m pytest tests/ -v           # Run tests
uv run ruff check src/ tests/               # Lint
uv run ruff check src/ tests/ --fix         # Auto-fix
uv run python -m mypy src/ --ignore-missing-imports  # Types

# Server
uv run uvicorn research_tool.main:app --reload

# Context Management
/clear                    # Reset (between tasks)
/compact                  # Summarize (at 70%)
/context                  # Show usage
```

---

## ENFORCEMENT CHECKLIST

<CRITICAL>
Before EVERY response, verify ALL of these:
</CRITICAL>

- [ ] Did I read existing code before suggesting changes?
- [ ] Did I use TodoWrite for task tracking?
- [ ] Did I run tests before claiming success?
- [ ] Did I show evidence for my claims?
- [ ] Did I avoid ALL banned phrases?
- [ ] Is my chunk size ≤3 files?
- [ ] Did I commit after verification?
- [ ] Did I update TODO.md?

**If ANY checkbox is unchecked, FIX IT before responding.**

---

## REMINDER: RULES APPLY ALWAYS

<CRITICAL>
These rules apply to:
- Every response
- Every code change
- Every claim
- Every session

There are NO exceptions.
"Just this once" = violation.
"It's a small change" = violation.
"I'll test later" = violation.
</CRITICAL>

---

*This file is law. Follow it exactly.*
*Violations trigger "AIRPORT" reset.*
*Last updated: 2025-12-09*

---

## Sources

- [Anthropic Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)
- [Claude Code Setup Templates](https://github.com/centminmod/my-claude-code-setup)
- [Claude Rules Template](https://gist.github.com/tsdevau/673876d17d344f97ba3473bc081bd1e5)
