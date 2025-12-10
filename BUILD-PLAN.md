# RESEARCH TOOL — BUILD PLAN

> ## ⚠️ ADVARSEL: DETTE DOKUMENT ER FORÆLDET
>
> **Brug i stedet:** `docs/plans/2025-12-10-professional-research-scraper.md`
>
> Dette dokument var del af original build-plan men projektet har placeholders
> der skal fixes. Se CLAUDE.md for aktuel status.
>
> **Opdateret:** 2025-12-10

---

## Step-by-Step Execution Instructions for Claude Code

**Authority**: This plan implements SPEC.md which operationalizes META-BUILD-GUIDE-v2.md
**Execution Mode**: Full autonomous
**Workspace**: /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
**Repository**: https://github.com/memouritsen-ui/solid-robot.git

---

## EXECUTION RULES FOR CLAUDE CODE

### Rule 1: Document Reference
Before ANY code generation, read and reference:
1. META-BUILD-GUIDE-v2.md (constitutional authority)
2. SPEC.md (specification)
3. The relevant phase document (/docs/phase-X.md)
4. TODO.md (current task)

### Rule 2: No Deviation
- DO NOT add features not in SPEC.md
- DO NOT change architecture decisions
- DO NOT skip validation steps
- If uncertain, STOP and document the question in DECISIONS.md

### Rule 3: TDD Mandatory
For every implementation task:
1. Write failing test FIRST
2. Implement minimum code to pass
3. Refactor while green
4. Never commit code without passing tests

### Rule 4: Validation After Every Step
After each code generation:
1. Run tests: `cd backend && uv run pytest`
2. Run linter: `cd backend && uv run ruff check .`
3. Run type check: `cd backend && uv run mypy .`
4. If ANY fail, fix before proceeding

### Rule 5: Commit Discipline
- Commit after each completed task
- Format: `type(scope): description [TODO.md #X]`
- Example: `feat(search): implement Tavily provider [TODO.md #23]`

### Rule 6: Branch Strategy
```
main (protected)
└── develop
    ├── phase-1-foundation
    ├── phase-2-conversational
    ├── phase-3-memory
    ├── phase-4-research
    ├── phase-5-intelligence
    ├── phase-6-export
    └── phase-7-polish
```

### Rule 7: Error Recovery
If a step fails after 3 attempts:
1. Document failure in ERROR-LOG.md
2. Check ERROR-HANDLING.md for recovery procedure
3. If no procedure exists, STOP and wait for user

---

## PRE-BUILD SETUP

### Step 0.1: Initialize Repository Structure

```bash
cd /Users/madsbruusgaard-mouritsen/solid-robot

# Create directory structure
mkdir -p docs
mkdir -p gui/ResearchTool/ResearchTool/{App,Views,ViewModels,Services,Models,Resources}
mkdir -p gui/ResearchTool/ResearchToolTests/{ViewModelTests,ServiceTests}
mkdir -p backend/src/research_tool/{api/routes,api/websocket,api/middleware}
mkdir -p backend/src/research_tool/{core,models,utils}
mkdir -p backend/src/research_tool/services/{llm,search,memory,export}
mkdir -p backend/src/research_tool/agent/{nodes,tools,decisions}
mkdir -p backend/tests/{unit,integration,e2e}
mkdir -p backend/templates
mkdir -p backend/data/domain_configs
mkdir -p scripts
mkdir -p .github/workflows
```

### Step 0.2: Copy Documentation

Copy all build documents to repository:
- SPEC.md → /
- BUILD-PLAN.md → /
- TODO.md → /
- CHECKLIST.md → /
- CLAUDE-CODE-INSTRUCTIONS.md → /
- ERROR-HANDLING.md → /
- MERGELOG.md → /
- META-BUILD-GUIDE-v2.md → /docs/

### Step 0.3: Initialize Git

```bash
git checkout -b develop
git add .
git commit -m "chore: initialize project structure and documentation"
git push -u origin develop
```

### Step 0.4: Create Branch for Phase 1

```bash
git checkout -b phase-1-foundation develop
```

---

## PHASE 1: FOUNDATION

**Branch**: phase-1-foundation
**Duration**: ~2-3 hours
**Validation Gate**: Section 6.3 Phase 1 checkpoint in META guide

### Step 1.1: Python Project Setup

**Reference**: TODO.md #1-5

```bash
cd backend

# Initialize with uv
uv init

# Create pyproject.toml with dependencies
```

Create `/backend/pyproject.toml`:
```toml
[project]
name = "research-tool"
version = "0.1.0"
description = "Professional research assistant tool"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.23.0",
    "websockets>=11.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "httpx>=0.24.0",
    "litellm>=1.0.0",
    "langgraph>=0.0.30",
    "langchain-core>=0.1.0",
    "lancedb>=0.3.0",
    "sentence-transformers>=2.2.0",
    "networkx>=3.0",
    "tenacity>=8.2.0",
    "structlog>=23.0.0",
    "python-multipart>=0.0.6",
    "jinja2>=3.1.0",
    "weasyprint>=60.0",
    "python-docx>=0.8.11",
    "python-pptx>=0.6.21",
    "openpyxl>=3.1.0",
    "playwright>=1.40.0",
    "tavily-python>=0.3.0",
    "arxiv>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "pytest-benchmark>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "bandit>=1.7.0",
    "pre-commit>=3.4.0",
]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

```bash
# Install dependencies
uv sync
uv pip install -e ".[dev]"

# Verify installation
uv run python -c "import fastapi; import langgraph; import lancedb; print('OK')"
```

**Validation**: Dependencies install without error

### Step 1.2: Create Core Configuration

**Reference**: TODO.md #6-8, META guide Section 4.1.3

Create `/backend/src/research_tool/__init__.py`:
```python
"""Research Tool - Professional research assistant."""
__version__ = "0.1.0"
```

Create `/backend/src/research_tool/core/__init__.py`:
```python
"""Core configuration and utilities."""
from .config import Settings
from .exceptions import ResearchToolError
from .logging import get_logger

__all__ = ["Settings", "ResearchToolError", "get_logger"]
```

Create `/backend/src/research_tool/core/config.py`:
```python
"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # API Keys
    tavily_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    exa_api_key: Optional[str] = None
    brave_api_key: Optional[str] = None
    semantic_scholar_api_key: Optional[str] = None
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_num_parallel: int = 4
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    
    # Paths
    data_dir: str = "./data"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

Create `/backend/src/research_tool/core/exceptions.py`:
```python
"""Exception hierarchy for Research Tool."""


class ResearchToolError(Exception):
    """Base exception for all Research Tool errors."""
    pass


class ConfigurationError(ResearchToolError):
    """Configuration or setup error."""
    pass


class NetworkError(ResearchToolError):
    """Network-related error."""
    pass


class RateLimitError(NetworkError):
    """Rate limit exceeded."""
    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class AccessDeniedError(NetworkError):
    """Access denied (403, login required)."""
    pass


class TimeoutError(NetworkError):
    """Request timeout."""
    pass


class ParseError(ResearchToolError):
    """Failed to parse response."""
    pass


class StorageError(ResearchToolError):
    """Storage operation failed."""
    pass


class ModelError(ResearchToolError):
    """LLM-related error."""
    pass


class ModelUnavailableError(ModelError):
    """Model not available."""
    pass


class ModelOverloadedError(ModelError):
    """Model overloaded."""
    pass


class ResearchError(ResearchToolError):
    """Research process error."""
    pass


class SaturationNotReached(ResearchError):
    """Research stopped before saturation."""
    pass


class SourceExhausted(ResearchError):
    """All sources exhausted."""
    pass
```

Create `/backend/src/research_tool/core/logging.py`:
```python
"""Structured logging configuration."""
import structlog
from typing import Any


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a configured logger."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger(name)
```

**Validation**: 
```bash
cd backend
uv run python -c "from research_tool.core import Settings, get_logger; print('OK')"
```

### Step 1.3: Create FastAPI Application Shell

**Reference**: TODO.md #9-12

Create `/backend/src/research_tool/main.py`:
```python
"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from research_tool.core import Settings, get_logger

settings = Settings()
logger = get_logger(__name__)

app = FastAPI(
    title="Research Tool API",
    version="0.1.0",
    description="Professional research assistant backend"
)

# CORS for SwiftUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.on_event("startup")
async def startup():
    """Application startup."""
    logger.info("application_starting", host=settings.host, port=settings.port)


@app.on_event("shutdown")
async def shutdown():
    """Application shutdown."""
    logger.info("application_shutting_down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
```

**Validation**:
```bash
cd backend
uv run python -m research_tool.main &
sleep 2
curl http://localhost:8000/api/health
# Should return: {"status":"healthy","version":"0.1.0"}
kill %1
```

### Step 1.4: Create Test Framework

**Reference**: TODO.md #13-15

Create `/backend/tests/__init__.py`:
```python
"""Test suite for Research Tool."""
```

Create `/backend/tests/conftest.py`:
```python
"""Pytest fixtures and configuration."""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from research_tool.main import app


@pytest.fixture
def client():
    """Synchronous test client."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Asynchronous test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

Create `/backend/tests/unit/__init__.py`:
```python
"""Unit tests."""
```

Create `/backend/tests/unit/test_health.py`:
```python
"""Test health endpoint."""
import pytest


def test_health_check(client):
    """Health endpoint returns healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
```

**Validation**:
```bash
cd backend
uv run pytest tests/unit/test_health.py -v
# Should pass
```

### Step 1.5: Setup Linting and Type Checking

**Reference**: TODO.md #16-18

Create `/backend/.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic>=2.0]
```

**Validation**:
```bash
cd backend
uv run ruff check .
uv run mypy src/
# Both should pass with no errors
```

### Step 1.6: Create SwiftUI Project Shell

**Reference**: TODO.md #19-25

Create Xcode project at `/gui/ResearchTool/`:

Create `/gui/ResearchTool/ResearchTool/App/ResearchToolApp.swift`:
```swift
import SwiftUI

@main
struct ResearchToolApp: App {
    @StateObject private var appState = AppState()
    
    var body: some Scene {
        WindowGroup {
            MainView()
                .environmentObject(appState)
        }
    }
}
```

Create `/gui/ResearchTool/ResearchTool/App/AppState.swift`:
```swift
import Foundation
import Combine

@MainActor
class AppState: ObservableObject {
    @Published var isBackendConnected: Bool = false
    @Published var currentView: ViewType = .chat
    
    enum ViewType {
        case chat
        case settings
        case export
    }
    
    private var healthCheckTimer: Timer?
    
    init() {
        startHealthCheck()
    }
    
    private func startHealthCheck() {
        // Check backend health every 5 seconds
        healthCheckTimer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                await self?.checkBackendHealth()
            }
        }
        // Initial check
        Task {
            await checkBackendHealth()
        }
    }
    
    private func checkBackendHealth() async {
        guard let url = URL(string: "http://localhost:8000/api/health") else { return }
        
        do {
            let (_, response) = try await URLSession.shared.data(from: url)
            if let httpResponse = response as? HTTPURLResponse {
                isBackendConnected = httpResponse.statusCode == 200
            }
        } catch {
            isBackendConnected = false
        }
    }
}
```

Create `/gui/ResearchTool/ResearchTool/Views/MainView.swift`:
```swift
import SwiftUI

struct MainView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        NavigationSplitView {
            // Sidebar
            List {
                NavigationLink(destination: ChatView()) {
                    Label("Chat", systemImage: "message")
                }
                NavigationLink(destination: SettingsView()) {
                    Label("Settings", systemImage: "gear")
                }
            }
            .navigationTitle("Research Tool")
        } detail: {
            ChatView()
        }
        .toolbar {
            ToolbarItem(placement: .automatic) {
                HStack {
                    Circle()
                        .fill(appState.isBackendConnected ? Color.green : Color.red)
                        .frame(width: 8, height: 8)
                    Text(appState.isBackendConnected ? "Connected" : "Disconnected")
                        .font(.caption)
                }
            }
        }
    }
}
```

Create `/gui/ResearchTool/ResearchTool/Views/ChatView.swift`:
```swift
import SwiftUI

struct ChatView: View {
    @StateObject private var viewModel = ChatViewModel()
    @State private var inputText: String = ""
    
    var body: some View {
        VStack {
            // Messages
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 12) {
                    ForEach(viewModel.messages) { message in
                        MessageBubble(message: message)
                    }
                }
                .padding()
            }
            
            // Input
            HStack {
                TextField("Ask anything...", text: $inputText)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit {
                        sendMessage()
                    }
                
                Button(action: sendMessage) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title2)
                }
                .disabled(inputText.isEmpty || viewModel.isLoading)
            }
            .padding()
        }
        .navigationTitle("Chat")
    }
    
    private func sendMessage() {
        guard !inputText.isEmpty else { return }
        let text = inputText
        inputText = ""
        Task {
            await viewModel.sendMessage(text)
        }
    }
}
```

Create `/gui/ResearchTool/ResearchTool/Views/MessageBubble.swift`:
```swift
import SwiftUI

struct MessageBubble: View {
    let message: Message
    
    var body: some View {
        HStack {
            if message.role == .user {
                Spacer()
            }
            
            Text(message.content)
                .padding(12)
                .background(message.role == .user ? Color.blue : Color.gray.opacity(0.2))
                .foregroundColor(message.role == .user ? .white : .primary)
                .cornerRadius(16)
            
            if message.role == .assistant {
                Spacer()
            }
        }
    }
}
```

Create `/gui/ResearchTool/ResearchTool/Views/SettingsView.swift`:
```swift
import SwiftUI

struct SettingsView: View {
    var body: some View {
        Form {
            Section("Privacy Mode") {
                Text("Settings coming in Phase 2")
            }
        }
        .navigationTitle("Settings")
    }
}
```

Create `/gui/ResearchTool/ResearchTool/Models/Message.swift`:
```swift
import Foundation

struct Message: Identifiable {
    let id: UUID
    let role: Role
    let content: String
    let timestamp: Date
    
    enum Role {
        case user
        case assistant
    }
    
    init(role: Role, content: String) {
        self.id = UUID()
        self.role = role
        self.content = content
        self.timestamp = Date()
    }
}
```

Create `/gui/ResearchTool/ResearchTool/ViewModels/ChatViewModel.swift`:
```swift
import Foundation

@MainActor
class ChatViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var isLoading: Bool = false
    
    private let baseURL = "http://localhost:8000"
    
    func sendMessage(_ text: String) async {
        // Add user message
        let userMessage = Message(role: .user, content: text)
        messages.append(userMessage)
        
        isLoading = true
        defer { isLoading = false }
        
        // TODO: Implement WebSocket streaming in Phase 2
        // For now, just echo back
        let response = Message(role: .assistant, content: "Backend connection coming in Phase 2. You said: \(text)")
        messages.append(response)
    }
}
```

**Validation**:
1. Open Xcode project
2. Build (Cmd+B) - should succeed
3. Run (Cmd+R) - app should launch with "Disconnected" indicator
4. Start backend, indicator should turn green

### Step 1.7: Create Scripts

**Reference**: TODO.md #26-28

Create `/scripts/setup.sh`:
```bash
#!/bin/bash
set -e

echo "=== Research Tool Setup ==="

# Check prerequisites
command -v uv >/dev/null 2>&1 || { echo "uv required. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
command -v ollama >/dev/null 2>&1 || { echo "ollama required. Install: brew install ollama"; exit 1; }

# Setup Python backend
echo "Setting up Python backend..."
cd backend
uv sync
uv pip install -e ".[dev]"

# Install playwright browsers
uv run playwright install chromium

# Create .env if not exists
if [ ! -f .env ]; then
    cp ../.env.example .env
    echo "Created .env from template. Please add your API keys."
fi

echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Add API keys to backend/.env"
echo "2. Run: ./scripts/start_ollama.sh"
echo "3. Run: ./scripts/start_backend.sh"
echo "4. Open gui/ResearchTool in Xcode and run"
```

Create `/scripts/start_backend.sh`:
```bash
#!/bin/bash
cd "$(dirname "$0")/../backend"
uv run uvicorn research_tool.main:app --reload --host 127.0.0.1 --port 8000
```

Create `/scripts/start_ollama.sh`:
```bash
#!/bin/bash

# Set environment for optimal performance (from META guide Section 3.2)
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KEEP_ALIVE=5m
export OLLAMA_MAX_LOADED_MODELS=2

# Start Ollama service
ollama serve
```

Create `/scripts/run_tests.sh`:
```bash
#!/bin/bash
cd "$(dirname "$0")/../backend"

echo "=== Running Tests ==="
uv run pytest tests/ -v --cov=src/research_tool --cov-report=term-missing

echo "=== Running Linter ==="
uv run ruff check .

echo "=== Running Type Check ==="
uv run mypy src/

echo "=== Running Security Scan ==="
uv run bandit -r src/
```

```bash
chmod +x scripts/*.sh
```

### Step 1.8: Phase 1 Validation Gate

**Reference**: META guide Section 6.3 - After Phase 1

```
□ SwiftUI sends message to FastAPI and receives response
  → Verified: Health check shows connected
□ All linting passes with zero warnings
  → Run: cd backend && uv run ruff check .
□ Test framework runs and reports coverage
  → Run: cd backend && uv run pytest --cov
□ Build produces working .app bundle
  → Build and run in Xcode
□ No code exists that violates Anti-Patterns
  → Manual review of all code
```

**Commit and Merge**:
```bash
git add .
git commit -m "feat: complete phase 1 foundation [BUILD-PLAN Phase 1]"
git checkout develop
git merge phase-1-foundation
git push origin develop
```

---

## PHASE 2: CONVERSATIONAL CORE

**Branch**: phase-2-conversational
**Duration**: ~3-4 hours
**Validation Gate**: Section 6.3 Phase 2 checkpoint in META guide

```bash
git checkout -b phase-2-conversational develop
```

### Step 2.1: Implement LLM Provider Interface

**Reference**: TODO.md #29-33, META guide Section 4.2.3

Create `/backend/src/research_tool/services/llm/__init__.py`:
```python
"""LLM service providers."""
from .provider import ModelProvider
from .router import LLMRouter
from .selector import ModelSelector

__all__ = ["ModelProvider", "LLMRouter", "ModelSelector"]
```

Create `/backend/src/research_tool/services/llm/provider.py`:
```python
"""Abstract interface for LLM providers."""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Union


class ModelProvider(ABC):
    """Abstract interface for LLM providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this provider."""
        pass
    
    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> Union[str, AsyncIterator[str]]:
        """Generate completion."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if model is loaded/accessible."""
        pass
    
    @abstractmethod
    def get_context_window(self) -> int:
        """Return max context length."""
        pass
    
    @abstractmethod
    def requires_privacy(self) -> bool:
        """True if this is a local model."""
        pass
```

### Step 2.2: Implement LiteLLM Router

**Reference**: TODO.md #34-38, META guide Section 3.3

Create `/backend/src/research_tool/services/llm/router.py`:
```python
"""LiteLLM Router implementation."""
from typing import AsyncIterator, Optional
from litellm import Router, acompletion
import os

from research_tool.core import Settings, get_logger
from research_tool.core.exceptions import ModelUnavailableError

logger = get_logger(__name__)
settings = Settings()


class LLMRouter:
    """LiteLLM-based model router with fallback support."""
    
    def __init__(self):
        self.router = Router(
            model_list=[
                {
                    "model_name": "local-fast",
                    "litellm_params": {
                        "model": "ollama/llama3.1:8b-instruct-q8_0",
                        "api_base": settings.ollama_base_url
                    }
                },
                {
                    "model_name": "local-powerful",
                    "litellm_params": {
                        "model": "ollama/qwen2.5:32b-instruct-q5_K_M",
                        "api_base": settings.ollama_base_url
                    }
                },
                {
                    "model_name": "cloud-best",
                    "litellm_params": {
                        "model": "claude-3-5-sonnet-20241022",
                        "api_key": settings.anthropic_api_key
                    }
                }
            ],
            fallbacks=[
                {"local-powerful": ["cloud-best"]},
                {"cloud-best": ["local-powerful"]}
            ],
            set_verbose=False
        )
    
    async def complete(
        self,
        messages: list[dict],
        model: str = "local-fast",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> str | AsyncIterator[str]:
        """
        Generate completion using specified model.
        
        Args:
            messages: Chat messages
            model: Model name (local-fast, local-powerful, cloud-best)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            
        Returns:
            Generated text or async iterator of tokens
        """
        try:
            if stream:
                return self._stream_completion(messages, model, temperature, max_tokens)
            else:
                response = await self.router.acompletion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error("completion_failed", model=model, error=str(e))
            raise ModelUnavailableError(f"Failed to get completion: {e}")
    
    async def _stream_completion(
        self,
        messages: list[dict],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        response = await self.router.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def is_model_available(self, model: str) -> bool:
        """Check if a model is available."""
        try:
            await self.router.acompletion(
                model=model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except:
            return False
```

### Step 2.3: Implement Model Selector

**Reference**: TODO.md #39-42, META guide Section 7.1

Create `/backend/src/research_tool/services/llm/selector.py`:
```python
"""Model selection logic based on task and privacy requirements."""
from enum import Enum
from dataclasses import dataclass

from research_tool.core import get_logger

logger = get_logger(__name__)


class PrivacyMode(Enum):
    """Privacy mode settings."""
    LOCAL_ONLY = "local_only"
    CLOUD_ALLOWED = "cloud_allowed"
    HYBRID = "hybrid"


class TaskComplexity(Enum):
    """Task complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ModelRecommendation:
    """Model selection recommendation."""
    model: str
    reasoning: str
    privacy_compliant: bool


class ModelSelector:
    """
    Select appropriate model based on task complexity and privacy requirements.
    
    Implements decision tree from META guide Section 7.1.
    """
    
    def select(
        self,
        task_complexity: TaskComplexity,
        privacy_mode: PrivacyMode,
        available_models: list[str] | None = None
    ) -> ModelRecommendation:
        """
        Select the best model for the task.
        
        Decision tree from META guide Section 7.1:
        
        1. If privacy_mode == LOCAL_ONLY:
           - High complexity → local-powerful
           - Otherwise → local-fast
           - NEVER fall back to cloud
           
        2. If privacy_mode == CLOUD_ALLOWED:
           - High complexity → cloud-best (fallback: local-powerful)
           - Medium complexity → local-powerful
           - Low complexity → local-fast
           
        3. If privacy_mode == HYBRID:
           - Apply specific rules per data type (future implementation)
        """
        available = available_models or ["local-fast", "local-powerful", "cloud-best"]
        
        if privacy_mode == PrivacyMode.LOCAL_ONLY:
            # CRITICAL: Never use cloud models
            if task_complexity == TaskComplexity.HIGH:
                if "local-powerful" in available:
                    return ModelRecommendation(
                        model="local-powerful",
                        reasoning="High complexity task with local-only privacy requirement. Using most capable local model.",
                        privacy_compliant=True
                    )
                elif "local-fast" in available:
                    return ModelRecommendation(
                        model="local-fast",
                        reasoning="High complexity task but local-powerful unavailable. Using local-fast with potential quality trade-off.",
                        privacy_compliant=True
                    )
                else:
                    raise ValueError("No local models available but LOCAL_ONLY privacy mode set")
            else:
                if "local-fast" in available:
                    return ModelRecommendation(
                        model="local-fast",
                        reasoning="Lower complexity task with local-only privacy. Using fast local model.",
                        privacy_compliant=True
                    )
                else:
                    raise ValueError("No local models available but LOCAL_ONLY privacy mode set")
        
        elif privacy_mode == PrivacyMode.CLOUD_ALLOWED:
            if task_complexity == TaskComplexity.HIGH:
                if "cloud-best" in available:
                    return ModelRecommendation(
                        model="cloud-best",
                        reasoning="High complexity task with cloud allowed. Using most capable model for best results.",
                        privacy_compliant=True
                    )
                elif "local-powerful" in available:
                    return ModelRecommendation(
                        model="local-powerful",
                        reasoning="High complexity task but cloud unavailable. Falling back to local-powerful.",
                        privacy_compliant=True
                    )
            elif task_complexity == TaskComplexity.MEDIUM:
                if "local-powerful" in available:
                    return ModelRecommendation(
                        model="local-powerful",
                        reasoning="Medium complexity task. Local-powerful provides good balance of capability and privacy.",
                        privacy_compliant=True
                    )
            else:
                if "local-fast" in available:
                    return ModelRecommendation(
                        model="local-fast",
                        reasoning="Low complexity task. Using fast model for efficiency.",
                        privacy_compliant=True
                    )
        
        # Fallback
        return ModelRecommendation(
            model=available[0],
            reasoning=f"Fallback selection. Using first available model: {available[0]}",
            privacy_compliant=privacy_mode != PrivacyMode.LOCAL_ONLY or "cloud" not in available[0]
        )
    
    def recommend_privacy_mode(
        self,
        query: str,
        has_sensitive_data: bool = False
    ) -> tuple[PrivacyMode, str]:
        """
        Recommend privacy mode based on query analysis.
        
        Returns:
            Tuple of (recommended mode, reasoning)
        """
        # Simple heuristics for now - can be enhanced with NLP
        sensitive_keywords = [
            "confidential", "private", "internal", "secret",
            "proprietary", "nda", "personal", "medical", "financial"
        ]
        
        query_lower = query.lower()
        found_sensitive = [kw for kw in sensitive_keywords if kw in query_lower]
        
        if has_sensitive_data or found_sensitive:
            return (
                PrivacyMode.LOCAL_ONLY,
                f"Detected potentially sensitive content ({', '.join(found_sensitive) if found_sensitive else 'marked as sensitive'}). Recommending local-only processing."
            )
        
        # For general queries, cloud is fine
        return (
            PrivacyMode.CLOUD_ALLOWED,
            "No sensitive content detected. Cloud processing allowed for best results."
        )
```

### Step 2.4: Implement Chat WebSocket

**Reference**: TODO.md #43-48, META guide Section 4.4

Create `/backend/src/research_tool/api/websocket/__init__.py`:
```python
"""WebSocket handlers."""
from .chat_ws import chat_websocket

__all__ = ["chat_websocket"]
```

Create `/backend/src/research_tool/api/websocket/chat_ws.py`:
```python
"""Chat WebSocket handler with streaming support."""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional
import json

from research_tool.core import get_logger
from research_tool.services.llm import LLMRouter, ModelSelector, PrivacyMode, TaskComplexity

logger = get_logger(__name__)


class ChatWebSocketHandler:
    """Handles chat WebSocket connections with streaming."""
    
    def __init__(self):
        self.router = LLMRouter()
        self.selector = ModelSelector()
        self.conversation_history: list[dict] = []
    
    async def handle(self, websocket: WebSocket):
        """Handle WebSocket connection."""
        await websocket.accept()
        logger.info("websocket_connected")
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_json()
                message = data.get("message", "")
                privacy_mode = PrivacyMode(data.get("privacy_mode", "cloud_allowed"))
                
                # Add to history
                self.conversation_history.append({
                    "role": "user",
                    "content": message
                })
                
                # Select model
                recommendation = self.selector.select(
                    task_complexity=TaskComplexity.MEDIUM,  # TODO: Analyze complexity
                    privacy_mode=privacy_mode
                )
                
                logger.info(
                    "model_selected",
                    model=recommendation.model,
                    reasoning=recommendation.reasoning
                )
                
                # Stream response
                full_response = ""
                async for token in await self.router.complete(
                    messages=self.conversation_history,
                    model=recommendation.model,
                    stream=True
                ):
                    full_response += token
                    await websocket.send_json({
                        "type": "token",
                        "content": token
                    })
                
                # Signal completion
                await websocket.send_json({
                    "type": "done",
                    "model": recommendation.model,
                    "reasoning": recommendation.reasoning
                })
                
                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_response
                })
                
        except WebSocketDisconnect:
            logger.info("websocket_disconnected")
        except Exception as e:
            logger.error("websocket_error", error=str(e))
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
            except:
                pass


async def chat_websocket(websocket: WebSocket):
    """WebSocket endpoint for chat."""
    handler = ChatWebSocketHandler()
    await handler.handle(websocket)
```

Update `/backend/src/research_tool/main.py` to add WebSocket:
```python
# Add at top
from research_tool.api.websocket import chat_websocket

# Add route
app.websocket("/ws/chat")(chat_websocket)
```

### Step 2.5: Update SwiftUI WebSocket Client

**Reference**: TODO.md #49-54

Update `/gui/ResearchTool/ResearchTool/Services/WebSocketClient.swift`:
```swift
import Foundation

actor WebSocketClient {
    private var webSocket: URLSessionWebSocketTask?
    private let baseURL = "ws://localhost:8000"
    var onToken: ((String) -> Void)?
    var onComplete: ((String, String) -> Void)?  // (model, reasoning)
    var onError: ((String) -> Void)?
    
    func connect() {
        let url = URL(string: "\(baseURL)/ws/chat")!
        webSocket = URLSession.shared.webSocketTask(with: url)
        webSocket?.resume()
        receiveMessages()
    }
    
    func disconnect() {
        webSocket?.cancel(with: .goingAway, reason: nil)
        webSocket = nil
    }
    
    func send(message: String, privacyMode: String = "cloud_allowed") async throws {
        let payload: [String: Any] = [
            "message": message,
            "privacy_mode": privacyMode
        ]
        let data = try JSONSerialization.data(withJSONObject: payload)
        let string = String(data: data, encoding: .utf8)!
        try await webSocket?.send(.string(string))
    }
    
    private func receiveMessages() {
        webSocket?.receive { [weak self] result in
            Task {
                switch result {
                case .success(let message):
                    await self?.handleMessage(message)
                    self?.receiveMessages()
                case .failure(let error):
                    await self?.onError?(error.localizedDescription)
                }
            }
        }
    }
    
    private func handleMessage(_ message: URLSessionWebSocketTask.Message) async {
        guard case .string(let text) = message,
              let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = json["type"] as? String else {
            return
        }
        
        switch type {
        case "token":
            if let content = json["content"] as? String {
                await onToken?(content)
            }
        case "done":
            let model = json["model"] as? String ?? "unknown"
            let reasoning = json["reasoning"] as? String ?? ""
            await onComplete?(model, reasoning)
        case "error":
            if let errorMsg = json["message"] as? String {
                await onError?(errorMsg)
            }
        default:
            break
        }
    }
}
```

Update ChatViewModel to use WebSocket:
```swift
import Foundation

@MainActor
class ChatViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var isLoading: Bool = false
    @Published var currentResponse: String = ""
    @Published var lastModelUsed: String = ""
    @Published var privacyMode: String = "cloud_allowed"
    
    private let wsClient = WebSocketClient()
    
    init() {
        Task {
            await setupWebSocket()
        }
    }
    
    private func setupWebSocket() async {
        await wsClient.connect()
        
        await wsClient.onToken = { [weak self] token in
            Task { @MainActor in
                self?.currentResponse += token
            }
        }
        
        await wsClient.onComplete = { [weak self] model, reasoning in
            Task { @MainActor in
                guard let self = self else { return }
                let response = Message(role: .assistant, content: self.currentResponse)
                self.messages.append(response)
                self.currentResponse = ""
                self.lastModelUsed = model
                self.isLoading = false
            }
        }
        
        await wsClient.onError = { [weak self] error in
            Task { @MainActor in
                self?.isLoading = false
                // Handle error
            }
        }
    }
    
    func sendMessage(_ text: String) async {
        let userMessage = Message(role: .user, content: text)
        messages.append(userMessage)
        isLoading = true
        currentResponse = ""
        
        do {
            try await wsClient.send(message: text, privacyMode: privacyMode)
        } catch {
            isLoading = false
        }
    }
}
```

### Step 2.6: Write Tests for Phase 2

**Reference**: TODO.md #55-60

Create `/backend/tests/unit/test_llm_router.py`:
```python
"""Tests for LLM Router."""
import pytest
from unittest.mock import AsyncMock, patch

from research_tool.services.llm import LLMRouter, ModelSelector, PrivacyMode, TaskComplexity


class TestModelSelector:
    """Tests for model selection logic."""
    
    def test_local_only_high_complexity_selects_local_powerful(self):
        """LOCAL_ONLY + HIGH → local-powerful."""
        selector = ModelSelector()
        result = selector.select(
            task_complexity=TaskComplexity.HIGH,
            privacy_mode=PrivacyMode.LOCAL_ONLY
        )
        assert result.model == "local-powerful"
        assert result.privacy_compliant
        assert "cloud" not in result.model
    
    def test_local_only_never_selects_cloud(self):
        """LOCAL_ONLY should never return cloud model."""
        selector = ModelSelector()
        for complexity in TaskComplexity:
            result = selector.select(
                task_complexity=complexity,
                privacy_mode=PrivacyMode.LOCAL_ONLY
            )
            assert "cloud" not in result.model
            assert result.privacy_compliant
    
    def test_cloud_allowed_high_complexity_prefers_cloud(self):
        """CLOUD_ALLOWED + HIGH → cloud-best."""
        selector = ModelSelector()
        result = selector.select(
            task_complexity=TaskComplexity.HIGH,
            privacy_mode=PrivacyMode.CLOUD_ALLOWED
        )
        assert result.model == "cloud-best"
    
    def test_cloud_allowed_low_complexity_uses_fast(self):
        """CLOUD_ALLOWED + LOW → local-fast for efficiency."""
        selector = ModelSelector()
        result = selector.select(
            task_complexity=TaskComplexity.LOW,
            privacy_mode=PrivacyMode.CLOUD_ALLOWED
        )
        assert result.model == "local-fast"
    
    def test_recommendation_includes_reasoning(self):
        """All recommendations include reasoning."""
        selector = ModelSelector()
        for privacy in PrivacyMode:
            for complexity in TaskComplexity:
                try:
                    result = selector.select(complexity, privacy)
                    assert result.reasoning
                    assert len(result.reasoning) > 0
                except ValueError:
                    pass  # Expected for some combinations without available models


class TestPrivacyRecommendation:
    """Tests for privacy mode recommendation."""
    
    def test_sensitive_keywords_trigger_local_only(self):
        """Sensitive keywords should recommend LOCAL_ONLY."""
        selector = ModelSelector()
        
        sensitive_queries = [
            "Analyze this confidential report",
            "Review my private medical records",
            "Process internal company data",
        ]
        
        for query in sensitive_queries:
            mode, reasoning = selector.recommend_privacy_mode(query)
            assert mode == PrivacyMode.LOCAL_ONLY
    
    def test_general_queries_allow_cloud(self):
        """General queries should allow cloud processing."""
        selector = ModelSelector()
        
        general_queries = [
            "What is the capital of France?",
            "Explain quantum computing",
            "Find research papers on machine learning",
        ]
        
        for query in general_queries:
            mode, reasoning = selector.recommend_privacy_mode(query)
            assert mode == PrivacyMode.CLOUD_ALLOWED
```

### Step 2.7: Phase 2 Validation Gate

**Reference**: META guide Section 6.3 - After Phase 2

```
□ Can converse with local Qwen model
  → Test: Send message with LOCAL_ONLY mode
□ Can converse with Claude API  
  → Test: Send message with CLOUD_ALLOWED mode
□ Model switching works without conversation loss
  → Test: Switch modes mid-conversation
□ Streaming displays tokens as they arrive
  → Visual verification in GUI
□ Response time: <2s first token local, <1s cloud
  → Benchmark test
□ Privacy mode enforced correctly
  → Test: LOCAL_ONLY never calls cloud
□ All Anti-Patterns checked and not present
  → Review against META guide Section 5.5
```

**Commit and Merge**:
```bash
git add .
git commit -m "feat: complete phase 2 conversational core [BUILD-PLAN Phase 2]"
git checkout develop
git merge phase-2-conversational
git push origin develop
```

---

## PHASES 3-7: ABBREVIATED STRUCTURE

Due to document length, phases 3-7 follow the same pattern. Full details in:
- `/docs/phase-3-memory.md`
- `/docs/phase-4-research.md`
- `/docs/phase-5-intelligence.md`
- `/docs/phase-6-export.md`
- `/docs/phase-7-polish.md`

### Phase 3: Memory System
- Implement LanceDB vector storage
- Implement SQLite structured storage
- Implement memory repository interface
- Implement source effectiveness tracking
- Implement access failure recording
- **Validation**: Retrieval <100ms for 10K docs

### Phase 4: Research Agent
- Implement LangGraph workflow
- Implement all search providers (Tavily, Exa, Semantic Scholar, etc.)
- Implement rate limiting per provider
- Implement obstacle handling (rate limits, CAPTCHAs, paywalls)
- Implement saturation detection
- **Validation**: Complete research cycle executes

### Phase 5: Intelligence Features
- Implement domain detection
- Implement auto-configuration
- Implement privacy mode recommendation
- Implement cross-verification
- Implement confidence scoring
- Implement learning updates
- **Validation**: Learning influences future research

### Phase 6: Export System
- Implement all export formats (MD, JSON, PDF, DOCX, PPTX, XLSX)
- Implement Jinja2 template system
- Implement contextual template selection
- **Validation**: Each format produces valid files

### Phase 7: Polish and Integration
- End-to-end testing
- Performance optimization
- Documentation
- Edge case handling
- **Validation**: All 8 success criteria verified

---

## FINAL VALIDATION

Before declaring build complete:

1. Run full test suite: `./scripts/run_tests.sh`
2. Verify all 8 success criteria with evidence
3. Verify all anti-patterns NOT present
4. Verify all performance benchmarks met
5. Complete user acceptance testing
6. Update all documentation

---

*END OF BUILD PLAN*
