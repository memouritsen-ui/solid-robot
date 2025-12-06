# ERROR HANDLING PROCEDURES
## Recovery Guide for Common Build Failures

**Purpose**: When something goes wrong, consult this document for recovery procedures.

---

## 1. DEPENDENCY ERRORS

### 1.1 uv sync fails

**Symptoms**:
```
error: Failed to resolve dependencies
```

**Recovery**:
```bash
# Clear cache and retry
rm -rf .venv
uv cache clean
uv sync

# If still failing, check pyproject.toml for version conflicts
# Look for: incompatible version ranges, missing packages
```

### 1.2 Import error after install

**Symptoms**:
```
ModuleNotFoundError: No module named 'xxx'
```

**Recovery**:
```bash
# Verify package is installed
uv pip list | grep xxx

# If not listed, add to pyproject.toml and sync
uv add xxx
uv sync

# If listed but still failing, reinstall
uv pip install --force-reinstall xxx
```

### 1.3 Version conflict

**Symptoms**:
```
ERROR: Cannot install xxx==1.0 and yyy==2.0 because...
```

**Recovery**:
```bash
# Check what's requesting conflicting versions
uv pip show xxx
uv pip show yyy

# Update pyproject.toml with compatible versions
# Or use version ranges: "xxx>=1.0,<2.0"
```

---

## 2. TEST FAILURES

### 2.1 Test fails consistently

**Symptoms**:
```
FAILED tests/unit/test_something.py::test_function - AssertionError
```

**Recovery**:
1. Read the test carefully - what is it actually testing?
2. Read the implementation - does it match META guide requirements?
3. Check if test is correct against SPEC
4. Fix implementation (not test) unless test is wrong
5. If unsure, log in DECISIONS.md and ask user

### 2.2 Test passes locally, fails in CI

**Symptoms**: Test passes with `pytest` but fails in GitHub Actions

**Recovery**:
```bash
# Check for environment differences
# Common causes:
# - Hardcoded paths
# - Missing environment variables
# - Timing-dependent tests
# - External service dependencies

# Fix: Use fixtures, mock external services, use relative paths
```

### 2.3 Flaky test (sometimes passes, sometimes fails)

**Symptoms**: Inconsistent test results

**Recovery**:
```bash
# Identify flakiness
uv run pytest tests/path/to/test.py -v --count=10

# Common causes:
# - Race conditions (use proper async handling)
# - Random data (use seeds)
# - Time-dependent (mock time)
# - External services (mock them)

# Fix the root cause, don't just retry
```

### 2.4 Test hangs indefinitely

**Symptoms**: pytest never completes

**Recovery**:
```bash
# Run with timeout
uv run pytest tests/ --timeout=30

# Common causes:
# - Infinite loop in implementation
# - Blocking I/O without timeout
# - Deadlock in async code

# Fix: Add timeouts to all I/O operations
```

---

## 3. LINT/TYPE ERRORS

### 3.1 Ruff errors

**Symptoms**:
```
error: xxx.py:10:1: E501 Line too long
```

**Recovery**:
```bash
# Many errors auto-fixable
uv run ruff check . --fix

# For remaining errors, fix manually
# Reference: https://docs.astral.sh/ruff/rules/
```

### 3.2 Mypy errors

**Symptoms**:
```
error: xxx.py:10: error: Incompatible types in assignment
```

**Recovery**:
```bash
# Read error carefully - mypy is usually right

# Common fixes:
# 1. Add type hints
def func(x: int) -> str:

# 2. Use Optional for nullable
from typing import Optional
def func(x: Optional[int] = None):

# 3. Use Union for multiple types
from typing import Union
def func(x: Union[int, str]):

# 4. Use cast() for known-safe casts
from typing import cast
y = cast(int, x)

# 5. Use # type: ignore as LAST RESORT (document why)
x = something()  # type: ignore[assignment]  # Reason: ...
```

### 3.3 Missing type stubs

**Symptoms**:
```
error: Cannot find implementation or library stub for module named "xxx"
```

**Recovery**:
```bash
# Check if stubs exist
uv pip install types-xxx

# If no stubs, add to mypy config:
# In pyproject.toml:
[tool.mypy]
ignore_missing_imports = true

# Or per-module:
[[tool.mypy.overrides]]
module = "xxx.*"
ignore_missing_imports = true
```

---

## 4. OLLAMA ERRORS

### 4.1 Ollama not running

**Symptoms**:
```
ConnectionRefusedError: [Errno 61] Connection refused
```

**Recovery**:
```bash
# Start Ollama
./scripts/start_ollama.sh

# Or manually:
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_FLASH_ATTENTION=1
ollama serve
```

### 4.2 Model not found

**Symptoms**:
```
Error: model 'qwen2.5:32b-instruct-q5_K_M' not found
```

**Recovery**:
```bash
# Pull the model
ollama pull qwen2.5:32b-instruct-q5_K_M

# Verify
ollama list
```

### 4.3 Out of memory

**Symptoms**:
```
Error: not enough memory
```

**Recovery**:
```bash
# Check current memory usage
ollama ps

# Unload other models
ollama stop other-model

# If still failing, use smaller quantization or smaller model
ollama pull qwen2.5:32b-instruct-q4_K_M  # Smaller than q5
```

### 4.4 Slow performance

**Symptoms**: <10 tok/s instead of expected 15-20 tok/s

**Recovery**:
```bash
# Verify environment variables set
echo $OLLAMA_FLASH_ATTENTION  # Should be 1

# Verify not running in Docker
ps aux | grep ollama  # Should be native process

# Check GPU is being used
# In Ollama output, should see "metal" or "gpu"

# Increase Metal memory limit if needed
sudo sysctl iogpu.wired_limit_mb=40960
```

---

## 5. API ERRORS

### 5.1 Rate limit (429)

**Symptoms**:
```
HTTPError: 429 Too Many Requests
```

**Recovery**:
```python
# Implementation should handle this automatically via retry
# If happening frequently:
# 1. Check rate limiter is working
# 2. Reduce request frequency
# 3. Add more aggressive backoff

# Verify retry is configured:
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(RateLimitError)
)
```

### 5.2 Authentication error (401/403)

**Symptoms**:
```
HTTPError: 401 Unauthorized
```

**Recovery**:
```bash
# Check API key is set
echo $TAVILY_API_KEY
echo $ANTHROPIC_API_KEY

# If not set, add to .env
cp .env.example .env
# Edit .env with actual keys

# Verify keys are valid (not expired, correct permissions)
```

### 5.3 Timeout

**Symptoms**:
```
TimeoutError: Request timed out
```

**Recovery**:
```python
# Increase timeout for slow operations
async with httpx.AsyncClient(timeout=60.0) as client:
    ...

# Or use streaming for long operations
# Never block indefinitely
```

### 5.4 Service unavailable (503)

**Symptoms**:
```
HTTPError: 503 Service Unavailable
```

**Recovery**:
```python
# This is temporary - retry should handle it
# If persistent, check service status page
# Fallback to alternative provider if available
```

---

## 6. DATABASE ERRORS

### 6.1 LanceDB connection error

**Symptoms**:
```
OSError: Cannot open database at ./data/...
```

**Recovery**:
```bash
# Check directory exists and is writable
mkdir -p data
chmod 755 data

# If corrupted, may need to recreate
rm -rf data/lance_db
# Restart app - will recreate
```

### 6.2 SQLite locked

**Symptoms**:
```
sqlite3.OperationalError: database is locked
```

**Recovery**:
```bash
# Check for other processes using DB
lsof data/research.db

# Kill stale connections
# Or use WAL mode in SQLite:
# PRAGMA journal_mode=WAL;

# Implement proper connection pooling
```

### 6.3 Migration needed

**Symptoms**: Schema mismatch after code update

**Recovery**:
```bash
# For development, simplest is recreate
rm data/research.db
# Restart - will create with new schema

# For production, would need proper migrations
# But this is dev environment
```

---

## 7. GIT ERRORS

### 7.1 Merge conflict

**Symptoms**:
```
CONFLICT (content): Merge conflict in xxx.py
```

**Recovery**:
```bash
# View conflicts
git diff

# Resolution priority:
# 1. Check SPEC for correct behavior
# 2. Check META guide for requirements
# 3. Keep code that matches spec

# After resolving:
git add xxx.py
git commit -m "fix: resolve merge conflict per SPEC"
```

### 7.2 Accidentally committed to wrong branch

**Symptoms**: Commits on main/develop that should be on feature branch

**Recovery**:
```bash
# If not pushed yet:
git reset --soft HEAD~1  # Undo commit, keep changes
git stash
git checkout correct-branch
git stash pop
git commit -m "..."

# If already pushed - ask user for help
# Do NOT force push to shared branches
```

### 7.3 Lost work

**Symptoms**: Changes disappeared

**Recovery**:
```bash
# Check reflog
git reflog

# Find the commit with your work
git checkout abc1234

# Or check stash
git stash list
git stash show -p stash@{0}
```

---

## 8. SWIFTUI ERRORS

### 8.1 Build error - missing file

**Symptoms**:
```
error: Missing file: xxx.swift
```

**Recovery**:
1. Check file exists in correct location
2. Check file is added to Xcode project (not just filesystem)
3. In Xcode: File > Add Files to "ResearchTool"

### 8.2 Preview crash

**Symptoms**: SwiftUI preview won't load

**Recovery**:
1. Clean build folder (Cmd+Shift+K)
2. Restart Xcode
3. Check preview code has sample data
4. Simplify preview until it works

### 8.3 App won't connect to backend

**Symptoms**: "Disconnected" indicator stays red

**Recovery**:
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Check correct port in SwiftUI code
# Check firewall isn't blocking localhost

# In SwiftUI, verify URL:
let baseURL = "http://localhost:8000"  # Not 127.0.0.1
```

---

## 9. PHASE VALIDATION FAILURES

### 9.1 Validation gate not passing

**Symptoms**: Phase complete but validation fails

**Recovery**:
1. Go through CHECKLIST.md item by item
2. For each failing item:
   - Check implementation against SPEC
   - Check implementation against META guide
   - Run specific test for that requirement
3. Fix implementation
4. Re-run validation

### 9.2 Anti-pattern detected

**Symptoms**: Code review shows anti-pattern

**Recovery**:
1. Identify which anti-pattern (META guide Section 5)
2. Read the "RIGHT" example
3. Refactor code to match correct pattern
4. Add test that would catch the anti-pattern
5. Verify with reviewer

---

## 10. WHEN ALL ELSE FAILS

### 10.1 Nuclear Option (Development Only)

If the codebase is in an unrecoverable state:

```bash
# Save what you can
git stash
cp -r backend/tests /tmp/tests_backup

# Start fresh from last known good state
git fetch origin
git checkout develop
git reset --hard origin/develop

# Restore tests if they were good
cp -r /tmp/tests_backup/* backend/tests/

# Restart from current phase
```

### 10.2 Escalate to User

Document in DECISIONS.md:
```markdown
## BLOCKED - Need User Help

**Date**: [current date]

**Task**: TODO.md #[number]

**Problem**: [Clear description]

**What I Tried**:
1. [Attempt 1]
2. [Attempt 2]
3. [Attempt 3]

**Error Messages**:
```
[paste full error]
```

**Questions**:
1. [What you need to know]

**Status**: BLOCKED - Awaiting user response
```

Then STOP and wait.

---

*END OF ERROR HANDLING PROCEDURES*
