# CLAUDE.md - Research Tool Project

## CRITICAL: READ THIS FIRST

YOU MUST follow these rules. No exceptions. No rationalizations.

---

## ANTI-SYCOPHANCY RULES

**BANNED PHRASES** - Never use these:
- "You're absolutely right!"
- "That's a great idea!"
- "Excellent suggestion!"
- "That looks perfect!"
- "Great job!"

**REQUIRED BEHAVIOR**:
- Give honest technical assessment, not validation
- Point out flaws BEFORE implementing
- Say "This won't work because X" when true
- Disagree when the user is wrong
- Ask clarifying questions instead of assuming

**If you catch yourself agreeing automatically, STOP and reconsider.**

---

## MANDATORY WORKFLOW: EXPLORE → PLAN → CODE → TEST → COMMIT

### Phase 1: EXPLORE (Read before writing)
```
1. Read relevant source files
2. Read existing tests
3. Understand current implementation
4. Identify dependencies and side effects
```
**YOU MUST NOT write code until you understand existing code.**

### Phase 2: PLAN (Think before coding)
```
1. Use "ultrathink" for complex tasks
2. Write plan in TODO format
3. Break into chunks of 1-3 files max
4. Identify tests needed
5. Get approval before proceeding
```
**Use TodoWrite to track ALL tasks. No mental tracking.**

### Phase 3: CODE (Small chunks only)
```
1. Maximum 3 files per chunk
2. Write tests FIRST (TDD)
3. Implement minimal code to pass tests
4. Run verification after EACH file
```
**NEVER implement more than one feature at a time.**

### Phase 4: TEST (Verify before claiming done)
```bash
# Run ALL of these before claiming anything works:
cd /Users/madsbruusgaard-mouritsen/solid-robot/backend
uv run python -m pytest tests/ -v
uv run ruff check src/ tests/
uv run python -m mypy src/ --ignore-missing-imports
```
**ALL must pass. No exceptions. No "it mostly works".**

### Phase 5: COMMIT (Only after verification)
```
1. Only commit when ALL tests pass
2. Use conventional commit format
3. Update TODO.md with accurate status
```

---

## CHUNK-BASED DEVELOPMENT (Survives Auto-Compaction)

### Why Chunks Matter
Auto-compaction triggers at ~95% context. Large tasks get lost.
Small chunks = recoverable progress.

### Chunk Rules
| Chunk Size | Files | Tests | Commit |
|------------|-------|-------|--------|
| Small | 1 file | 2-5 tests | Yes |
| Medium | 2-3 files | 5-10 tests | Yes |
| Large | FORBIDDEN | - | - |

### After Each Chunk
1. Run all verification commands
2. Commit with descriptive message
3. Update TODO.md
4. Use `/compact` manually if context > 70%

### Recovery Protocol
If compaction happens mid-task:
1. Read TODO.md for current status
2. Read last commit message
3. Run tests to see what's broken
4. Continue from last verified state

---

## FORBIDDEN PRACTICES (Quick-Fixes)

### NEVER DO THESE:
- [ ] Claim "done" without running tests
- [ ] Create placeholder/stub implementations
- [ ] Skip test coverage for new code
- [ ] Mark TODOs complete without verification
- [ ] Trust file existence = working code
- [ ] Use `--dangerously-skip-permissions`
- [ ] Implement without reading existing code first
- [ ] Make "small fixes" without tests
- [ ] Batch multiple features in one commit

### IF TEMPTED TO SHORTCUT:
Ask yourself: "Would this survive a code review?"
If no, don't do it.

---

## VERIFICATION REQUIREMENTS

### Before ANY Claim of Completion
```bash
# Tests (must show "216+ passed")
uv run python -m pytest tests/ -v

# Linting (must show "All checks passed!")
uv run ruff check src/ tests/

# Type checking (must show "Success")
uv run python -m mypy src/ --ignore-missing-imports
```

### Evidence-Based Claims Only
- "Tests pass" = Show pytest output
- "No lint errors" = Show ruff output
- "Types correct" = Show mypy output
- "Feature works" = Show test that proves it

---

## CONTEXT MANAGEMENT

### Strategic Compaction
- Use `/clear` between unrelated tasks
- Manual `/compact` at 70% context (don't wait for 95%)
- Add summary to TODO.md before compacting

### Memory Checkpoints
Before any large operation:
```
1. Update TODO.md with current progress
2. Commit all working code
3. Then proceed with large operation
```

### If Context Gets Large
```
/compact Focus on: current task, recent changes, test status
```

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
│   └── tests/         # pytest tests (216+ tests)
├── gui/               # SwiftUI macOS app
│   └── ResearchTool/
├── TODO.md            # Task tracking (KEEP UPDATED)
└── CLAUDE.md          # This file (READ FIRST)
```

---

## CURRENT STATUS

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 0-3 | COMPLETE | 100% |
| Phase 4 | PARTIAL | ~75% |
| Phase 5-7 | NOT STARTED | 0% |

**See TODO.md for detailed task breakdown.**

---

## TEST-DRIVEN DEVELOPMENT (TDD)

### The Only Acceptable Pattern
```
1. Write test that describes expected behavior
2. Run test → MUST FAIL (red)
3. Write minimal code to pass
4. Run test → MUST PASS (green)
5. Refactor if needed
6. Commit
```

### Why TDD is Mandatory
- Proves you understand the requirement
- Prevents "it works on my machine"
- Creates documentation via tests
- Catches regressions immediately

---

## SKILLS TO USE

When relevant, invoke these skills:

| Skill | When to Use |
|-------|-------------|
| `superpowers:brainstorming` | Before designing new features |
| `superpowers:test-driven-development` | Before writing any code |
| `superpowers:systematic-debugging` | When encountering bugs |
| `superpowers:verification-before-completion` | Before claiming done |
| `superpowers:requesting-code-review` | After completing features |

---

## COMMANDS REFERENCE

```bash
# Development
cd backend && uv run python -m pytest tests/ -v      # Run tests
cd backend && uv run ruff check src/ tests/          # Lint
cd backend && uv run ruff check src/ tests/ --fix    # Auto-fix lint
cd backend && uv run python -m mypy src/ --ignore-missing-imports  # Types

# Server
cd backend && uv run uvicorn research_tool.main:app --reload

# Context Management
/clear                    # Reset context (between tasks)
/compact                  # Summarize context (at 70%)
/context                  # Show context usage
```

---

## NEXT TASK PROTOCOL

When starting any task:

1. **Read** TODO.md for current status
2. **Pick** ONE uncompleted task
3. **Plan** using TodoWrite (break into chunks)
4. **Explore** relevant code first
5. **Test** write tests before implementation
6. **Implement** in small chunks
7. **Verify** run ALL verification commands
8. **Commit** only when verified
9. **Update** TODO.md with accurate status

---

## HONEST COMMUNICATION

### What to Say
- "This approach has these tradeoffs: ..."
- "I see a potential issue with ..."
- "Before implementing, I need to understand ..."
- "The tests show this is broken because ..."

### What NOT to Say
- "Looks great!" (without verification)
- "That should work!" (without testing)
- "Almost done!" (when tests fail)
- "Just a quick fix!" (without tests)

---

## ENFORCEMENT CHECKLIST

Before EVERY response, verify:
- [ ] Did I read existing code before suggesting changes?
- [ ] Did I run tests before claiming something works?
- [ ] Did I avoid banned sycophantic phrases?
- [ ] Did I use TodoWrite for task tracking?
- [ ] Is my chunk size ≤3 files?
- [ ] Did I commit after verification?

---

*This file is law. Follow it exactly.*
*Last updated: 2025-12-09*

## Sources & References

Best practices derived from:
- [Anthropic Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)
- [Claude Code Setup Templates](https://github.com/centminmod/my-claude-code-setup)
- [Claude Rules Template](https://gist.github.com/tsdevau/673876d17d344f97ba3473bc081bd1e5)
- [Claude Code Context Management](https://stevekinney.com/courses/ai-development/claude-code-compaction)
