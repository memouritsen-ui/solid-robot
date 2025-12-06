# PHASE 1: FOUNDATION
## Detailed Implementation Guide

**Prerequisites**: 
- META-BUILD-GUIDE-v2.md read and understood
- SPEC.md read and understood
- Repository initialized at /Users/madsbruusgaard-mouritsen/solid-robot

**Tasks**: TODO.md #1-47

**Estimated Duration**: 2-3 hours

---

## 1. OBJECTIVES

By the end of Phase 1:
- [ ] Python backend running with FastAPI
- [ ] SwiftUI shell displaying and connecting to backend
- [ ] Test framework operational
- [ ] Development tooling configured (linting, type checking)
- [ ] Scripts for common operations

---

## 2. DIRECTORY STRUCTURE

Create this exact structure (reference SPEC.md Section 2.2):

```
solid-robot/
├── docs/
│   └── META-BUILD-GUIDE-v2.md
├── gui/
│   └── ResearchTool/
│       ├── ResearchTool/
│       │   ├── App/
│       │   ├── Views/
│       │   ├── ViewModels/
│       │   ├── Services/
│       │   ├── Models/
│       │   └── Resources/
│       └── ResearchToolTests/
├── backend/
│   ├── src/
│   │   └── research_tool/
│   │       ├── core/
│   │       ├── api/
│   │       ├── models/
│   │       └── services/
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
├── scripts/
└── [documentation files]
```

---

## 3. PYTHON BACKEND SETUP

### 3.1 pyproject.toml

Create with these dependencies (see BUILD-PLAN.md Step 1.1 for complete file):

**Core Dependencies**:
- fastapi>=0.100.0
- uvicorn[standard]
- pydantic>=2.0
- pydantic-settings>=2.0
- httpx
- structlog

**Dev Dependencies**:
- pytest>=7.4.0
- pytest-cov
- pytest-asyncio
- ruff>=0.1.0
- mypy>=1.5.0
- bandit

### 3.2 Core Configuration Module

**Files to create**:
1. `/backend/src/research_tool/__init__.py` - Package init with version
2. `/backend/src/research_tool/core/__init__.py` - Core exports
3. `/backend/src/research_tool/core/config.py` - Settings class using pydantic-settings
4. `/backend/src/research_tool/core/exceptions.py` - Exception hierarchy (META guide Section 4.1.4)
5. `/backend/src/research_tool/core/logging.py` - structlog configuration

**Key Points**:
- Settings loads from environment and .env file
- Exception hierarchy matches META guide exactly
- Logging uses JSON format for structured output

### 3.3 FastAPI Application

**File**: `/backend/src/research_tool/main.py`

**Requirements**:
- CORS middleware configured for SwiftUI (allow all origins for localhost dev)
- Health endpoint at `/api/health`
- Startup/shutdown events with logging
- Entry point for uvicorn

### 3.4 Verification Commands

```bash
cd backend
uv sync
uv run python -c "from research_tool.core import Settings; print('OK')"
uv run uvicorn research_tool.main:app --host 127.0.0.1 --port 8000
curl http://localhost:8000/api/health
```

---

## 4. TEST FRAMEWORK

### 4.1 pytest Configuration

In `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 4.2 Fixtures

**File**: `/backend/tests/conftest.py`

Provide:
- `client` - Synchronous TestClient
- `async_client` - Async httpx client

### 4.3 First Test

**File**: `/backend/tests/unit/test_health.py`

Test that health endpoint returns:
- Status code 200
- JSON with "status": "healthy"
- JSON includes "version"

### 4.4 Verification

```bash
cd backend
uv run pytest tests/ -v
uv run pytest tests/ --cov=src/research_tool --cov-report=term-missing
```

---

## 5. LINTING AND TYPE CHECKING

### 5.1 Ruff Configuration

In `pyproject.toml`:
```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
```

### 5.2 Mypy Configuration

In `pyproject.toml`:
```toml
[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

### 5.3 Verification

```bash
cd backend
uv run ruff check .
uv run mypy src/
```

Both commands must return zero errors.

---

## 6. SWIFTUI PROJECT

### 6.1 Project Creation

Create Xcode project:
- Type: macOS App
- Interface: SwiftUI
- Language: Swift
- Location: `/gui/ResearchTool/`

### 6.2 Files to Create

**App Layer**:
- `ResearchToolApp.swift` - App entry point
- `AppState.swift` - Observable state object with backend health check

**Views Layer**:
- `MainView.swift` - NavigationSplitView layout
- `ChatView.swift` - Chat interface (placeholder)
- `MessageBubble.swift` - Message display component
- `SettingsView.swift` - Settings (placeholder)

**Models Layer**:
- `Message.swift` - Message data model

**ViewModels Layer**:
- `ChatViewModel.swift` - Chat logic (placeholder, full implementation in Phase 2)

### 6.3 Key Implementation Details

**AppState**:
- Timer-based health check every 5 seconds
- Published `isBackendConnected` boolean
- Hits `http://localhost:8000/api/health`

**MainView**:
- NavigationSplitView with sidebar
- Toolbar showing connection indicator (green/red dot)

### 6.4 Verification

1. Build project (Cmd+B) - no errors
2. Run project (Cmd+R) - app launches
3. Without backend: shows "Disconnected" (red)
4. With backend running: shows "Connected" (green)

---

## 7. SCRIPTS

### 7.1 setup.sh

- Check prerequisites (uv, ollama)
- Install Python dependencies
- Create .env from template
- Print next steps

### 7.2 start_backend.sh

- Change to backend directory
- Start uvicorn with reload

### 7.3 start_ollama.sh

- Set environment variables (META guide Section 3.2.1)
- Start ollama serve

### 7.4 run_tests.sh

- Run pytest with coverage
- Run ruff
- Run mypy
- Run bandit

### 7.5 Verification

```bash
chmod +x scripts/*.sh
./scripts/run_tests.sh
```

---

## 8. VALIDATION GATE

Before proceeding to Phase 2, verify (from META guide Section 6.3):

```
□ SwiftUI sends message to FastAPI and receives response
  → Health check shows "Connected" when backend running

□ All linting passes with zero warnings
  → uv run ruff check . returns no output

□ Test framework runs and reports coverage
  → uv run pytest --cov shows coverage report

□ Build produces working .app bundle
  → Xcode Archive succeeds (or at least Run succeeds)

□ No code exists that violates Anti-Patterns
  → Manual review completed
```

---

## 9. COMMIT AND MERGE

After validation passes:

```bash
git add .
git commit -m "feat: complete phase 1 foundation [BUILD-PLAN Phase 1]"
git checkout develop
git merge phase-1-foundation
git push origin develop
```

Update MERGELOG.md with merge details.

---

## 10. COMMON ISSUES

### Issue: uv not found
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.zshrc
```

### Issue: Xcode project won't build
- Verify all Swift files are added to project (File > Add Files)
- Clean build folder (Cmd+Shift+K)
- Check for syntax errors in SwiftUI views

### Issue: Backend won't start
- Check port 8000 is not in use: `lsof -i :8000`
- Verify all imports resolve: `python -c "from research_tool.main import app"`

---

*END OF PHASE 1 GUIDE*
