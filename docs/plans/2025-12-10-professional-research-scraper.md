# SOLID-ROBOT Professional Research Scraper - Complete Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
> **KRITISK:** Følg HVERT trin PRÆCIST. Ingen improvisation. Ingen "forbedringer". KUN hvad der står.

**Goal:** Transformere SOLID-ROBOT fra prototype med placeholders til production-grade professional research scraper.

**Nuværende Status (ÆRLIG):**
- Infrastruktur: 90% (providers, export, config eksisterer)
- Research Pipeline Logic: ~40% (kun collect + plan er ægte implementeret)
- 3 nodes er TOM SHELL/PLACEHOLDER: process.py, analyze.py, synthesize.py
- Circuit breaker og retry eksisterer men er IKKE integreret i providers

**Architecture:**
- Python FastAPI backend med LangGraph workflow
- SwiftUI macOS frontend
- LiteLLM router til LLM (Claude cloud, Ollama local)
- Multiple search providers (Tavily, Brave, PubMed, arXiv, Semantic Scholar, etc.)

**Tech Stack:**
- Python 3.11, FastAPI, LangGraph, LiteLLM, Pydantic
- Swift 5.9, SwiftUI, WebSocket
- pytest, ruff, mypy

---

# FASE 1: FOUNDATION FIX

## Task 1.1: Fix BackendLauncher Path Resolution

**Problem:** Hardcoded path `/Users/madsbruusgaard-mouritsen/solid-robot/backend` (lowercase) matcher ikke `SOLID-ROBOT` (uppercase).

**Files:**
- Modify: `gui/ResearchTool/ResearchTool/Services/BackendLauncher.swift`

**Step 1: Åbn filen og find linje 16-29**

Nuværende kode:
```swift
private var backendPath: String {
    // First check if running from app bundle
    if let bundlePath = Bundle.main.resourcePath {
        let bundleBackendPath = (bundlePath as NSString)
            .deletingLastPathComponent
            .appending("/backend")
        if FileManager.default.fileExists(atPath: bundleBackendPath) {
            return bundleBackendPath
        }
    }

    // Fallback to development path
    return "/Users/madsbruusgaard-mouritsen/solid-robot/backend"
}
```

**Step 2: Erstat HELE `backendPath` property med denne kode**

```swift
/// Path to the backend directory with robust resolution
private var backendPath: String {
    // Priority 1: Environment variable
    if let envPath = ProcessInfo.processInfo.environment["RESEARCH_TOOL_BACKEND_PATH"] {
        if FileManager.default.fileExists(atPath: envPath) {
            print("[BackendLauncher] Using env path: \(envPath)")
            return envPath
        }
        print("[BackendLauncher] WARNING: Env path not found: \(envPath)")
    }

    // Priority 2: App bundle (for distributed app)
    if let bundlePath = Bundle.main.resourcePath {
        let bundleBackendPath = (bundlePath as NSString)
            .deletingLastPathComponent
            .appending("/backend")
        if FileManager.default.fileExists(atPath: bundleBackendPath) {
            print("[BackendLauncher] Using bundle path: \(bundleBackendPath)")
            return bundleBackendPath
        }
    }

    // Priority 3: UserDefaults custom path
    if let customPath = UserDefaults.standard.string(forKey: "backendPath") {
        if FileManager.default.fileExists(atPath: customPath) {
            print("[BackendLauncher] Using custom path: \(customPath)")
            return customPath
        }
        print("[BackendLauncher] WARNING: Custom path not found: \(customPath)")
    }

    // Priority 4: Known development paths (TRY BOTH CASINGS)
    let devPaths = [
        "/Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend",  // Uppercase (CORRECT)
        "/Users/madsbruusgaard-mouritsen/solid-robot/backend",  // Lowercase (fallback)
        NSHomeDirectory() + "/SOLID-ROBOT/backend",
        NSHomeDirectory() + "/solid-robot/backend"
    ]

    for path in devPaths {
        if FileManager.default.fileExists(atPath: path) {
            print("[BackendLauncher] Using dev path: \(path)")
            return path
        }
    }

    // Nothing found - return first dev path and let it fail with clear error
    let fallback = devPaths[0]
    print("[BackendLauncher] ERROR: No valid backend path found. Tried: \(devPaths)")
    return fallback
}
```

**Step 3: Tilføj fejlhåndtering i `startBackendIfNeeded()` - find linje 74 og erstat**

Find:
```swift
statusMessage = "Backend kunne ikke startes"
```

Erstat med:
```swift
statusMessage = "Backend kunne ikke startes. Tjek at backend findes i: \(backendPath)"
print("[BackendLauncher] FATAL: Backend startup failed after 30s. Path: \(backendPath)")
```

**Step 4: Gem filen**

**Step 5: Rebuild GUI**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/gui/ResearchTool
swift build -c release
```

Expected output: `Build complete!`

**Step 6: Commit**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
git add gui/ResearchTool/ResearchTool/Services/BackendLauncher.swift
git commit -m "fix(gui): robust backend path resolution with multiple fallbacks

- Add environment variable support (RESEARCH_TOOL_BACKEND_PATH)
- Add UserDefaults custom path support
- Fix case sensitivity (SOLID-ROBOT vs solid-robot)
- Add detailed logging for path resolution
- Add clear error message when no path found"
```

---

## Task 1.2: Create Environment Configuration

**Files:**
- Create: `backend/.env`
- Modify: `backend/.env.example`

**Step 1: Læs eksisterende .env.example**

```bash
cat /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/.env.example
```

**Step 2: Opret .env fil med din Anthropic key**

```bash
cat > /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/.env << 'EOF'
# Required API Keys
ANTHROPIC_API_KEY=your-anthropic-key-here

# Optional API Keys (add when available)
TAVILY_API_KEY=
BRAVE_API_KEY=
EXA_API_KEY=

# Optional: Email for Unpaywall API (free, no key needed)
UNPAYWALL_EMAIL=

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_NUM_PARALLEL=4

# Server Configuration
HOST=127.0.0.1
PORT=8000
DEBUG=false

# Paths
DATA_DIR=./data
EOF
```

**Step 3: VIGTIGT - Indsæt din RIGTIGE Anthropic API key**

Åbn filen og erstat `your-anthropic-key-here` med din faktiske key:
```bash
nano /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/.env
```

**Step 4: Verificer .env er i .gitignore**

```bash
grep "^\.env$" /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/.gitignore || echo ".env" >> /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/.gitignore
```

**Step 5: Opdater .env.example med dokumentation**

```bash
cat > /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/.env.example << 'EOF'
# =============================================================================
# SOLID-ROBOT Research Tool - Environment Configuration
# =============================================================================
# Copy this file to .env and fill in your values:
#   cp .env.example .env
#
# REQUIRED: At minimum, you need ANTHROPIC_API_KEY for the tool to function.
# Other keys enable additional search providers.
# =============================================================================

# -----------------------------------------------------------------------------
# REQUIRED: LLM API Key
# -----------------------------------------------------------------------------
# Get your key at: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-xxxxx

# -----------------------------------------------------------------------------
# OPTIONAL: Search Provider API Keys
# -----------------------------------------------------------------------------
# Tavily AI Search (recommended) - https://tavily.com/
# Provides high-quality web search with content extraction
TAVILY_API_KEY=tvly-xxxxx

# Brave Search API - https://brave.com/search/api/
# Alternative web search provider
BRAVE_API_KEY=BSA-xxxxx

# Exa AI Search - https://exa.ai/
# Neural search for finding similar content
EXA_API_KEY=exa-xxxxx

# Semantic Scholar API Key (optional, increases rate limit)
# https://www.semanticscholar.org/product/api
SEMANTIC_SCHOLAR_API_KEY=

# Unpaywall (free, just needs email for identification)
# https://unpaywall.org/products/api
UNPAYWALL_EMAIL=your-email@example.com

# -----------------------------------------------------------------------------
# LOCAL LLM: Ollama Configuration
# -----------------------------------------------------------------------------
# If you want to use local models, install Ollama: https://ollama.ai/
# Then pull models: ollama pull llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_NUM_PARALLEL=4

# -----------------------------------------------------------------------------
# Server Configuration
# -----------------------------------------------------------------------------
HOST=127.0.0.1
PORT=8000
DEBUG=false

# -----------------------------------------------------------------------------
# Data Storage
# -----------------------------------------------------------------------------
DATA_DIR=./data
EOF
```

**Step 6: Commit**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
git add backend/.env.example backend/.gitignore
git commit -m "docs(config): comprehensive .env.example with documentation

- Document all API keys with signup URLs
- Explain which are required vs optional
- Add Ollama configuration section
- Ensure .env is in .gitignore"
```

---

## Task 1.3: Implement Config Validation at Startup

**Files:**
- Modify: `backend/src/research_tool/core/config.py`

**Step 1: Læs nuværende config.py**

```bash
cat /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/src/research_tool/core/config.py
```

**Step 2: Erstat HELE filen med denne implementation**

```python
"""Application configuration with validation and status reporting."""

from enum import Enum
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from research_tool.core.logging import get_logger

logger = get_logger(__name__)


class FeatureStatus(Enum):
    """Status of optional features based on configuration."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    DEGRADED = "degraded"


class Settings(BaseSettings):
    """Application settings loaded from environment with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required API Keys
    anthropic_api_key: str | None = None

    # Optional Search Provider API Keys
    tavily_api_key: str | None = None
    exa_api_key: str | None = None
    brave_api_key: str | None = None
    semantic_scholar_api_key: str | None = None
    unpaywall_email: str | None = None

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_num_parallel: int = 4

    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    # Paths
    data_dir: str = "./data"

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str | None) -> str | None:
        """Validate Anthropic API key format."""
        if v and not v.startswith("sk-ant-"):
            logger.warning(
                "anthropic_key_format_warning",
                message="Anthropic API key should start with 'sk-ant-'"
            )
        return v

    @field_validator("tavily_api_key")
    @classmethod
    def validate_tavily_key(cls, v: str | None) -> str | None:
        """Validate Tavily API key format."""
        if v and not v.startswith("tvly-"):
            logger.warning(
                "tavily_key_format_warning",
                message="Tavily API key should start with 'tvly-'"
            )
        return v

    def get_feature_status(self) -> dict[str, FeatureStatus]:
        """Get status of all features based on configuration.

        Returns:
            dict mapping feature name to its status
        """
        return {
            "cloud_llm": (
                FeatureStatus.ENABLED if self.anthropic_api_key
                else FeatureStatus.DISABLED
            ),
            "tavily_search": (
                FeatureStatus.ENABLED if self.tavily_api_key
                else FeatureStatus.DISABLED
            ),
            "brave_search": (
                FeatureStatus.ENABLED if self.brave_api_key
                else FeatureStatus.DISABLED
            ),
            "exa_search": (
                FeatureStatus.ENABLED if self.exa_api_key
                else FeatureStatus.DISABLED
            ),
            "semantic_scholar": FeatureStatus.ENABLED,  # No key required
            "pubmed": FeatureStatus.ENABLED,  # No key required
            "arxiv": FeatureStatus.ENABLED,  # No key required
            "unpaywall": (
                FeatureStatus.ENABLED if self.unpaywall_email
                else FeatureStatus.DEGRADED
            ),
        }

    def get_missing_keys(self) -> list[str]:
        """Get list of missing but recommended API keys.

        Returns:
            list of missing key names with descriptions
        """
        missing = []

        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY (REQUIRED for cloud LLM)")
        if not self.tavily_api_key:
            missing.append("TAVILY_API_KEY (recommended for web search)")

        return missing

    def get_configured_keys(self) -> list[str]:
        """Get list of configured API keys.

        Returns:
            list of configured key names
        """
        configured = []

        if self.anthropic_api_key:
            configured.append("ANTHROPIC_API_KEY")
        if self.tavily_api_key:
            configured.append("TAVILY_API_KEY")
        if self.brave_api_key:
            configured.append("BRAVE_API_KEY")
        if self.exa_api_key:
            configured.append("EXA_API_KEY")
        if self.semantic_scholar_api_key:
            configured.append("SEMANTIC_SCHOLAR_API_KEY")
        if self.unpaywall_email:
            configured.append("UNPAYWALL_EMAIL")

        return configured

    def validate_at_startup(self) -> bool:
        """Validate configuration at startup and log status.

        Returns:
            True if minimum required config is present, False otherwise
        """
        logger.info("config_validation_start")

        # Log configured keys
        configured = self.get_configured_keys()
        logger.info(
            "config_keys_configured",
            keys=configured,
            count=len(configured)
        )

        # Log missing keys
        missing = self.get_missing_keys()
        if missing:
            logger.warning(
                "config_keys_missing",
                keys=missing,
                count=len(missing)
            )

        # Log feature status
        features = self.get_feature_status()
        for feature, status in features.items():
            if status == FeatureStatus.DISABLED:
                logger.warning(
                    "feature_disabled",
                    feature=feature,
                    reason="Missing API key"
                )
            elif status == FeatureStatus.DEGRADED:
                logger.warning(
                    "feature_degraded",
                    feature=feature,
                    reason="Optional config missing"
                )

        # Check minimum requirements
        is_valid = self.anthropic_api_key is not None

        if not is_valid:
            logger.error(
                "config_validation_failed",
                reason="ANTHROPIC_API_KEY is required but not set"
            )
        else:
            logger.info("config_validation_passed")

        return is_valid

    def to_safe_dict(self) -> dict[str, Any]:
        """Get configuration as dict with secrets masked.

        Returns:
            dict with sensitive values replaced with '***'
        """
        return {
            "anthropic_api_key": "***" if self.anthropic_api_key else None,
            "tavily_api_key": "***" if self.tavily_api_key else None,
            "brave_api_key": "***" if self.brave_api_key else None,
            "exa_api_key": "***" if self.exa_api_key else None,
            "semantic_scholar_api_key": "***" if self.semantic_scholar_api_key else None,
            "unpaywall_email": self.unpaywall_email,  # Email is not secret
            "ollama_base_url": self.ollama_base_url,
            "ollama_num_parallel": self.ollama_num_parallel,
            "host": self.host,
            "port": self.port,
            "debug": self.debug,
            "data_dir": self.data_dir,
        }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance.

    Returns:
        Settings instance
    """
    return settings
```

**Step 3: Kør linting og type check**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run ruff check src/research_tool/core/config.py
uv run python -m mypy src/research_tool/core/config.py --ignore-missing-imports
```

Expected output: `All checks passed!` og `Success: no issues found`

**Step 4: Test at config loader virker**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -c "
from research_tool.core.config import settings
print('Loaded settings:')
print(settings.to_safe_dict())
print()
print('Feature status:')
for k, v in settings.get_feature_status().items():
    print(f'  {k}: {v.value}')
print()
print('Validation:', 'PASSED' if settings.validate_at_startup() else 'FAILED')
"
```

**Step 5: Commit**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
git add backend/src/research_tool/core/config.py
git commit -m "feat(config): add validation and feature status reporting

- Add startup validation with clear error messages
- Add feature status based on configured keys
- Add safe dict method for logging (masks secrets)
- Add validators for API key formats
- Log missing and configured keys at startup"
```

---

## Task 1.4: Implement Deep Health Check

**Files:**
- Modify: `backend/src/research_tool/main.py`
- Create: `backend/src/research_tool/api/routes/health.py`

**Step 1: Opret health routes fil**

```bash
cat > /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/src/research_tool/api/routes/health.py << 'EOF'
"""Health check endpoints with deep dependency checking."""

from datetime import datetime
from enum import Enum
from typing import Any

import httpx
from fastapi import APIRouter

from research_tool.core.config import settings
from research_tool.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/health", tags=["health"])


class HealthStatus(str, Enum):
    """Health status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


async def check_ollama() -> dict[str, Any]:
    """Check Ollama availability.

    Returns:
        dict with status and details
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return {
                    "status": HealthStatus.HEALTHY,
                    "models_available": models,
                    "model_count": len(models)
                }
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": f"HTTP {response.status_code}"
            }
    except httpx.ConnectError:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": "Connection refused - is Ollama running?"
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e)
        }


async def check_anthropic() -> dict[str, Any]:
    """Check Anthropic API key validity.

    Returns:
        dict with status and details
    """
    if not settings.anthropic_api_key:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": "ANTHROPIC_API_KEY not configured"
        }

    # Just verify key format - don't make actual API call to save costs
    if settings.anthropic_api_key.startswith("sk-ant-"):
        return {
            "status": HealthStatus.HEALTHY,
            "key_configured": True,
            "key_format_valid": True
        }

    return {
        "status": HealthStatus.DEGRADED,
        "key_configured": True,
        "key_format_valid": False,
        "warning": "Key format unexpected (should start with sk-ant-)"
    }


async def check_search_providers() -> dict[str, Any]:
    """Check search provider availability.

    Returns:
        dict with status per provider
    """
    providers = {}

    # Tavily
    if settings.tavily_api_key:
        providers["tavily"] = {"status": HealthStatus.HEALTHY, "configured": True}
    else:
        providers["tavily"] = {"status": HealthStatus.DISABLED, "configured": False}

    # Brave
    if settings.brave_api_key:
        providers["brave"] = {"status": HealthStatus.HEALTHY, "configured": True}
    else:
        providers["brave"] = {"status": HealthStatus.DISABLED, "configured": False}

    # Free providers (always available)
    providers["semantic_scholar"] = {"status": HealthStatus.HEALTHY, "configured": True}
    providers["pubmed"] = {"status": HealthStatus.HEALTHY, "configured": True}
    providers["arxiv"] = {"status": HealthStatus.HEALTHY, "configured": True}

    return providers


@router.get("")
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint.

    Returns:
        dict with status and version
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/detailed")
async def detailed_health_check() -> dict[str, Any]:
    """Detailed health check with all dependencies.

    Returns:
        dict with status of all components
    """
    logger.info("detailed_health_check_start")

    # Check all components
    ollama_status = await check_ollama()
    anthropic_status = await check_anthropic()
    providers_status = await check_search_providers()

    # Determine overall status
    overall = HealthStatus.HEALTHY

    if anthropic_status["status"] == HealthStatus.UNHEALTHY:
        overall = HealthStatus.UNHEALTHY
    elif ollama_status["status"] == HealthStatus.UNHEALTHY:
        # Ollama is optional if Anthropic works
        if anthropic_status["status"] != HealthStatus.HEALTHY:
            overall = HealthStatus.DEGRADED

    # Count available search providers
    available_providers = sum(
        1 for p in providers_status.values()
        if p["status"] == HealthStatus.HEALTHY
    )
    if available_providers < 2:
        overall = HealthStatus.DEGRADED

    result = {
        "status": overall.value,
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "ollama": ollama_status,
            "anthropic": anthropic_status,
            "search_providers": providers_status
        },
        "summary": {
            "search_providers_available": available_providers,
            "llm_available": anthropic_status["status"] == HealthStatus.HEALTHY,
            "local_llm_available": ollama_status["status"] == HealthStatus.HEALTHY
        }
    }

    logger.info(
        "detailed_health_check_complete",
        overall_status=overall.value,
        providers_available=available_providers
    )

    return result


@router.get("/config")
async def config_status() -> dict[str, Any]:
    """Get current configuration status (safe, no secrets).

    Returns:
        dict with configuration status
    """
    feature_status = settings.get_feature_status()

    return {
        "config": settings.to_safe_dict(),
        "features": {k: v.value for k, v in feature_status.items()},
        "missing_keys": settings.get_missing_keys(),
        "configured_keys": settings.get_configured_keys()
    }
EOF
```

**Step 2: Opdater main.py til at bruge health router**

Åbn `backend/src/research_tool/main.py` og find linje 10-11:
```python
from research_tool.api.routes import export, research
```

Erstat med:
```python
from research_tool.api.routes import export, health, research
```

Find linje 60-61:
```python
app.include_router(research.router)
app.include_router(export.router)
```

Erstat med:
```python
app.include_router(health.router)
app.include_router(research.router)
app.include_router(export.router)
```

Find og SLET den gamle health_check funktion (linje 64-72):
```python
@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Dictionary with status and version.
    """
    return {"status": "healthy", "version": "0.1.0"}
```

**Step 3: Opdater routes __init__.py**

```bash
cat > /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/src/research_tool/api/routes/__init__.py << 'EOF'
"""API route modules."""

from research_tool.api.routes import export, health, research

__all__ = ["export", "health", "research"]
EOF
```

**Step 4: Tilføj config validation ved startup i main.py**

Find lifespan function og opdater den:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events.

    Args:
        app: FastAPI application instance.

    Yields:
        Nothing, but handles startup and shutdown.
    """
    # Startup
    logger.info("application_starting", host=settings.host, port=settings.port)

    # Validate configuration
    if not settings.validate_at_startup():
        logger.error(
            "startup_config_invalid",
            message="Configuration validation failed - some features may not work"
        )

    yield
    # Shutdown
    logger.info("application_shutting_down")
```

**Step 5: Kør linting og type check**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run ruff check src/research_tool/api/routes/health.py src/research_tool/main.py
uv run python -m mypy src/research_tool/api/routes/health.py src/research_tool/main.py --ignore-missing-imports
```

**Step 6: Test health endpoints**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run uvicorn src.research_tool.main:app --host 127.0.0.1 --port 8000 &
sleep 3
curl http://localhost:8000/api/health | python -m json.tool
curl http://localhost:8000/api/health/detailed | python -m json.tool
curl http://localhost:8000/api/health/config | python -m json.tool
kill %1
```

**Step 7: Commit**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
git add backend/src/research_tool/api/routes/health.py backend/src/research_tool/api/routes/__init__.py backend/src/research_tool/main.py
git commit -m "feat(health): implement deep health check with dependency status

- Add /api/health/detailed endpoint with all component status
- Add /api/health/config endpoint for configuration status
- Check Ollama availability and list models
- Check Anthropic API key configuration
- Check all search provider status
- Add config validation at startup
- Calculate overall health from component status"
```

---

## Task 1.5: Add Startup Self-Test

**Files:**
- Create: `backend/src/research_tool/core/startup.py`
- Modify: `backend/src/research_tool/main.py`

**Step 1: Opret startup self-test modul**

```bash
cat > /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/src/research_tool/core/startup.py << 'EOF'
"""Startup self-test to verify critical components."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from research_tool.core.config import settings
from research_tool.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StartupTestResult:
    """Result of a single startup test."""

    name: str
    passed: bool
    message: str
    duration_ms: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class StartupReport:
    """Complete startup test report."""

    tests: list[StartupTestResult]
    total_duration_ms: float
    all_passed: bool
    critical_failures: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "tests": [
                {
                    "name": t.name,
                    "passed": t.passed,
                    "message": t.message,
                    "duration_ms": t.duration_ms
                }
                for t in self.tests
            ],
            "total_duration_ms": self.total_duration_ms,
            "all_passed": self.all_passed,
            "critical_failures": self.critical_failures,
            "warnings": self.warnings
        }


async def test_data_directory() -> StartupTestResult:
    """Test that data directory exists and is writable."""
    start = datetime.now()

    data_dir = Path(settings.data_dir)

    try:
        # Create if not exists
        data_dir.mkdir(parents=True, exist_ok=True)

        # Test write
        test_file = data_dir / ".startup_test"
        test_file.write_text("test")
        test_file.unlink()

        duration = (datetime.now() - start).total_seconds() * 1000
        return StartupTestResult(
            name="data_directory",
            passed=True,
            message=f"Data directory OK: {data_dir.absolute()}",
            duration_ms=duration,
            details={"path": str(data_dir.absolute())}
        )
    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        return StartupTestResult(
            name="data_directory",
            passed=False,
            message=f"Data directory error: {e}",
            duration_ms=duration,
            details={"error": str(e)}
        )


async def test_domain_configs() -> StartupTestResult:
    """Test that domain configuration files exist."""
    start = datetime.now()

    data_dir = Path(settings.data_dir)
    config_dir = data_dir / "domain_configs"

    expected_configs = ["medical.json", "academic.json", "regulatory.json", "competitive_intelligence.json"]

    try:
        missing = []
        found = []

        for config in expected_configs:
            config_path = config_dir / config
            if config_path.exists():
                found.append(config)
            else:
                missing.append(config)

        duration = (datetime.now() - start).total_seconds() * 1000

        if missing:
            return StartupTestResult(
                name="domain_configs",
                passed=False,
                message=f"Missing domain configs: {missing}",
                duration_ms=duration,
                details={"found": found, "missing": missing}
            )

        return StartupTestResult(
            name="domain_configs",
            passed=True,
            message=f"All {len(found)} domain configs found",
            duration_ms=duration,
            details={"found": found}
        )
    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        return StartupTestResult(
            name="domain_configs",
            passed=False,
            message=f"Domain config error: {e}",
            duration_ms=duration,
            details={"error": str(e)}
        )


async def test_llm_configuration() -> StartupTestResult:
    """Test that at least one LLM is configured."""
    start = datetime.now()

    has_cloud = bool(settings.anthropic_api_key)
    has_local = False

    # Quick check for Ollama
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            has_local = response.status_code == 200
    except Exception:
        pass

    duration = (datetime.now() - start).total_seconds() * 1000

    if not has_cloud and not has_local:
        return StartupTestResult(
            name="llm_configuration",
            passed=False,
            message="No LLM available - need ANTHROPIC_API_KEY or running Ollama",
            duration_ms=duration,
            details={"cloud": has_cloud, "local": has_local}
        )

    return StartupTestResult(
        name="llm_configuration",
        passed=True,
        message=f"LLM available (cloud={has_cloud}, local={has_local})",
        duration_ms=duration,
        details={"cloud": has_cloud, "local": has_local}
    )


async def test_search_providers() -> StartupTestResult:
    """Test that at least one search provider is available."""
    start = datetime.now()

    available = []

    # Free providers are always available
    available.extend(["semantic_scholar", "pubmed", "arxiv"])

    # Check configured providers
    if settings.tavily_api_key:
        available.append("tavily")
    if settings.brave_api_key:
        available.append("brave")
    if settings.exa_api_key:
        available.append("exa")

    duration = (datetime.now() - start).total_seconds() * 1000

    return StartupTestResult(
        name="search_providers",
        passed=True,
        message=f"{len(available)} search providers available",
        duration_ms=duration,
        details={"available": available}
    )


async def run_startup_tests() -> StartupReport:
    """Run all startup tests and return report.

    Returns:
        StartupReport with all test results
    """
    logger.info("startup_tests_begin")
    start = datetime.now()

    # Run all tests
    tests = [
        test_data_directory,
        test_domain_configs,
        test_llm_configuration,
        test_search_providers,
    ]

    results = await asyncio.gather(*[t() for t in tests])

    # Analyze results
    critical_failures = []
    warnings = []

    for result in results:
        if not result.passed:
            if result.name in ["llm_configuration"]:
                critical_failures.append(f"{result.name}: {result.message}")
            else:
                warnings.append(f"{result.name}: {result.message}")

        # Log each result
        if result.passed:
            logger.info(
                "startup_test_passed",
                test=result.name,
                message=result.message,
                duration_ms=result.duration_ms
            )
        else:
            logger.warning(
                "startup_test_failed",
                test=result.name,
                message=result.message,
                duration_ms=result.duration_ms
            )

    total_duration = (datetime.now() - start).total_seconds() * 1000
    all_passed = len(critical_failures) == 0

    report = StartupReport(
        tests=results,
        total_duration_ms=total_duration,
        all_passed=all_passed,
        critical_failures=critical_failures,
        warnings=warnings
    )

    logger.info(
        "startup_tests_complete",
        all_passed=all_passed,
        total_duration_ms=total_duration,
        critical_failures=len(critical_failures),
        warnings=len(warnings)
    )

    return report
EOF
```

**Step 2: Opdater main.py lifespan til at køre startup tests**

I `main.py`, opdater lifespan funktionen:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events.

    Args:
        app: FastAPI application instance.

    Yields:
        Nothing, but handles startup and shutdown.
    """
    # Startup
    logger.info("application_starting", host=settings.host, port=settings.port)

    # Validate configuration
    if not settings.validate_at_startup():
        logger.error(
            "startup_config_invalid",
            message="Configuration validation failed - some features may not work"
        )

    # Run startup self-tests
    from research_tool.core.startup import run_startup_tests
    report = await run_startup_tests()

    if not report.all_passed:
        logger.error(
            "startup_tests_failed",
            critical_failures=report.critical_failures,
            warnings=report.warnings
        )

    yield
    # Shutdown
    logger.info("application_shutting_down")
```

**Step 3: Tilføj import øverst i main.py (efter andre imports)**

Tilføj denne import after eksisterende imports:
```python
# Note: run_startup_tests imported inside lifespan to avoid circular imports
```

**Step 4: Kør tests**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run ruff check src/research_tool/core/startup.py
uv run python -m mypy src/research_tool/core/startup.py --ignore-missing-imports
```

**Step 5: Commit**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
git add backend/src/research_tool/core/startup.py backend/src/research_tool/main.py
git commit -m "feat(startup): add self-test suite at application boot

- Test data directory existence and writability
- Test domain config files exist
- Test LLM availability (cloud or local)
- Test search provider configuration
- Generate startup report with pass/fail status
- Log all test results with timing
- Identify critical failures vs warnings"
```

---

# FASE 1 KOMPLET

**Verificer hele Fase 1:**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/ -v --tb=short -q | tail -10
uv run ruff check src/
uv run python -m mypy src/ --ignore-missing-imports | tail -5
```

---

# FASE 2: SEARCH PROVIDER INTEGRATION

## Task 2.1: Integrate Circuit Breaker into Base Provider

**Problem:** Circuit breaker eksisterer i `utils/circuit_breaker.py` men bruges IKKE i nogen providers.

**Files:**
- Modify: `backend/src/research_tool/services/search/provider.py`

**Step 1: Læs nuværende provider.py**

```bash
cat /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/src/research_tool/services/search/provider.py
```

**Step 2: Erstat HELE filen**

```python
"""Search provider abstract interface with circuit breaker and retry integration."""

from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, TypeVar

from research_tool.core.logging import get_logger
from research_tool.utils.circuit_breaker import get_circuit_breaker
from research_tool.utils.retry import with_retry

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def with_circuit_breaker(provider_name: str) -> Callable[[F], F]:
    """Decorator to wrap provider methods with circuit breaker.

    Args:
        provider_name: Name of the provider for circuit breaker lookup

    Returns:
        Decorated function with circuit breaker protection
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cb = get_circuit_breaker(provider_name)

            if not cb.can_execute():
                logger.warning(
                    "circuit_breaker_blocked",
                    provider=provider_name,
                    state=cb.state.value
                )
                return []  # Return empty results when circuit is open

            try:
                result = await func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                logger.error(
                    "provider_error_recorded",
                    provider=provider_name,
                    error=str(e),
                    failures=cb.failures
                )
                raise

        return wrapper  # type: ignore
    return decorator


class SearchProvider(ABC):
    """Abstract interface for search providers with built-in resilience."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this provider."""
        pass

    @property
    @abstractmethod
    def requests_per_second(self) -> float:
        """Rate limit for this provider (requests per second)."""
        pass

    @abstractmethod
    async def _do_search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Internal search implementation - override this in subclasses.

        Args:
            query: The search query
            max_results: Maximum number of results to return
            filters: Optional filters (provider-specific)

        Returns:
            list[dict]: List of result dictionaries
        """
        pass

    async def search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute search with circuit breaker and retry protection.

        This method wraps _do_search with:
        1. Circuit breaker to prevent cascade failures
        2. Retry logic with exponential backoff
        3. Logging of all operations

        Args:
            query: The search query
            max_results: Maximum number of results to return
            filters: Optional filters (provider-specific)

        Returns:
            list[dict]: List of result dictionaries with keys:
                - url: Result URL
                - title: Result title
                - snippet: Result snippet/abstract
                - source_name: Name of this provider
                - full_content: Optional full text content
                - metadata: Optional provider-specific metadata
        """
        cb = get_circuit_breaker(self.name)

        if not cb.can_execute():
            logger.warning(
                "search_blocked_circuit_open",
                provider=self.name,
                state=cb.state.value
            )
            return []

        try:
            logger.info(
                "search_start",
                provider=self.name,
                query=query[:50],
                max_results=max_results
            )

            results = await self._do_search(query, max_results, filters)

            cb.record_success()

            logger.info(
                "search_complete",
                provider=self.name,
                results_count=len(results)
            )

            return results

        except Exception as e:
            cb.record_failure()
            logger.error(
                "search_failed",
                provider=self.name,
                error=str(e),
                circuit_failures=cb.failures
            )
            raise

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is configured and accessible.

        Returns:
            bool: True if provider can be used
        """
        pass

    def get_circuit_status(self) -> dict[str, Any]:
        """Get current circuit breaker status for this provider.

        Returns:
            dict with circuit breaker state and failure count
        """
        cb = get_circuit_breaker(self.name)
        return {
            "state": cb.state.value,
            "failures": cb.failures,
            "failure_threshold": cb.failure_threshold
        }
```

**Step 3: Kør tests**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run ruff check src/research_tool/services/search/provider.py
uv run python -m mypy src/research_tool/services/search/provider.py --ignore-missing-imports
```

**Step 4: Commit**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
git add backend/src/research_tool/services/search/provider.py
git commit -m "feat(providers): integrate circuit breaker into base SearchProvider

- Add circuit breaker check before every search
- Record success/failure for circuit state
- Log circuit breaker blocks
- Add get_circuit_status() method
- Change search() to wrap _do_search() with protection"
```

---

## Task 2.2: Update Tavily Provider to Use New Interface

**Files:**
- Modify: `backend/src/research_tool/services/search/tavily.py`

**Step 1: Læs nuværende tavily.py**

```bash
cat /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/src/research_tool/services/search/tavily.py
```

**Step 2: Erstat HELE filen**

```python
"""Tavily AI search provider with circuit breaker protection."""

from datetime import datetime
from typing import Any

from tavily import TavilyClient

from research_tool.core.config import Settings
from research_tool.services.search.provider import SearchProvider
from research_tool.services.search.rate_limiter import rate_limiter
from research_tool.utils.retry import with_retry

settings = Settings()


class TavilyProvider(SearchProvider):
    """Tavily AI search provider with advanced search capabilities."""

    @property
    def name(self) -> str:
        """Provider identifier for Tavily."""
        return "tavily"

    @property
    def requests_per_second(self) -> float:
        """Rate limit: 5 RPS for Tavily API."""
        return 5.0

    def __init__(self) -> None:
        """Initialize Tavily client."""
        if not settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY not configured")
        self.client = TavilyClient(api_key=settings.tavily_api_key)

    @with_retry
    async def _do_search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute Tavily search with advanced mode.

        Args:
            query: Search query
            max_results: Maximum results to return
            filters: Optional filters (unused for Tavily)

        Returns:
            list[dict]: Standardized search results
        """
        await rate_limiter.acquire(self.name, self.requests_per_second)

        # Tavily search with advanced depth
        response = self.client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",  # More thorough search
            include_raw_content=True  # Get full content when available
        )

        results = []
        for r in response.get("results", []):
            results.append({
                "url": r["url"],
                "title": r["title"],
                "snippet": r["content"],
                "source_name": self.name,
                "full_content": r.get("raw_content"),
                "retrieved_at": datetime.now(),
                "metadata": {
                    "score": r.get("score", 0.0),
                    "published_date": r.get("published_date")
                }
            })

        return results

    async def is_available(self) -> bool:
        """Check if Tavily is configured and accessible.

        Returns:
            bool: True if API key is configured
        """
        return settings.tavily_api_key is not None
```

**Step 3: Kør tests**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run ruff check src/research_tool/services/search/tavily.py
uv run python -m pytest tests/unit/test_tavily.py -v
```

**Step 4: Commit**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
git add backend/src/research_tool/services/search/tavily.py
git commit -m "refactor(tavily): use new SearchProvider interface with _do_search

- Rename search() to _do_search() for circuit breaker wrapping
- Add @with_retry decorator for automatic retries
- Circuit breaker now integrated via base class"
```

---

## Task 2.3: Update ALL Other Providers

**Gentag Task 2.2 mønsteret for HVER provider:**

For HVER fil, skal du:
1. Rename `search()` til `_do_search()`
2. Tilføj `@with_retry` decorator
3. Fjern manuel circuit breaker kode hvis den findes

**Files to update:**
- `backend/src/research_tool/services/search/brave.py`
- `backend/src/research_tool/services/search/exa.py`
- `backend/src/research_tool/services/search/semantic_scholar.py`
- `backend/src/research_tool/services/search/pubmed.py`
- `backend/src/research_tool/services/search/arxiv.py`

**For hver fil, kør:**
```bash
uv run ruff check src/research_tool/services/search/<filename>.py
uv run python -m pytest tests/unit/test_<name>.py -v
```

**Commit efter HVER fil (max 3 filer per commit):**
```bash
git add backend/src/research_tool/services/search/<files>
git commit -m "refactor(<provider>): use new SearchProvider interface"
```

---

---

# FASE 3: RESEARCH PIPELINE NODES (KRITISK)

**DETTE ER DEN VIGTIGSTE FASE - Nodes er placeholders der skal implementeres fra bunden.**

## Task 3.1: Implement process_node with LLM Fact Extraction

**Problem:** Nuværende `process.py` genererer FAKE facts med hardcoded strenge.

**Files:**
- Modify: `backend/src/research_tool/agent/nodes/process.py`
- Create: `backend/tests/unit/test_process_node_llm.py`

**Step 1: Læs nuværende (broken) implementation**

```bash
cat /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/src/research_tool/agent/nodes/process.py
```

Nuværende output er FAKE:
```python
facts_extracted.append({
    "statement": f"Information found about: {entity.get('title', 'Unknown')}",
    ...
})
```

**Step 2: Skriv TEST først (TDD)**

```bash
cat > /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/tests/unit/test_process_node_llm.py << 'EOF'
"""Tests for process node with LLM fact extraction."""

import pytest

from research_tool.agent.nodes.process import (
    extract_facts_with_llm,
    process_node,
)


@pytest.fixture
def sample_entity():
    """Sample entity with full content."""
    return {
        "url": "https://example.com/article",
        "title": "Climate Change Effects on Agriculture",
        "snippet": "Rising temperatures affect crop yields...",
        "full_content": """
        Climate change is significantly impacting global agriculture.
        Studies show that wheat yields have decreased by 5.5% since 1980.
        The IPCC reports that temperatures have risen 1.1°C above pre-industrial levels.
        Farmers in the Midwest report earlier planting seasons by 2-3 weeks.
        Drought conditions have increased by 30% in the last decade.
        """,
        "source_name": "tavily",
        "metadata": {"score": 0.95}
    }


@pytest.fixture
def sample_state(sample_entity):
    """Sample research state with entities."""
    return {
        "original_query": "How does climate change affect agriculture?",
        "refined_query": "climate change agricultural impact crop yields",
        "domain": "academic",
        "entities_found": [sample_entity],
        "facts_extracted": [],
    }


class TestExtractFactsWithLLM:
    """Tests for LLM-based fact extraction."""

    @pytest.mark.asyncio
    async def test_extracts_facts_from_content(self, sample_entity):
        """Should extract factual statements from content."""
        facts = await extract_facts_with_llm(
            content=sample_entity["full_content"],
            source_url=sample_entity["url"],
            query_context="climate change agriculture"
        )

        assert len(facts) > 0
        for fact in facts:
            assert "statement" in fact
            assert "source" in fact
            assert "confidence" in fact
            assert fact["source"] == sample_entity["url"]
            assert 0 <= fact["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_empty_content_returns_empty(self):
        """Should return empty list for empty content."""
        facts = await extract_facts_with_llm(
            content="",
            source_url="https://example.com",
            query_context="test"
        )
        assert facts == []

    @pytest.mark.asyncio
    async def test_extracts_numerical_facts(self, sample_entity):
        """Should extract facts with numbers."""
        facts = await extract_facts_with_llm(
            content=sample_entity["full_content"],
            source_url=sample_entity["url"],
            query_context="climate statistics"
        )

        # Should find the 5.5%, 1.1°C, 30% facts
        numerical_facts = [f for f in facts if any(c.isdigit() for c in f["statement"])]
        assert len(numerical_facts) > 0


class TestProcessNode:
    """Tests for the process node."""

    @pytest.mark.asyncio
    async def test_process_node_extracts_facts(self, sample_state):
        """Should extract facts from all entities."""
        result = await process_node(sample_state)

        assert "facts_extracted" in result
        assert "current_phase" in result
        assert result["current_phase"] == "process"
        assert len(result["facts_extracted"]) > 0

    @pytest.mark.asyncio
    async def test_process_node_handles_missing_content(self):
        """Should handle entities without full_content gracefully."""
        state = {
            "original_query": "test query",
            "entities_found": [
                {"url": "https://example.com", "title": "Test", "snippet": "Short snippet"}
            ],
            "facts_extracted": [],
        }

        result = await process_node(state)
        # Should still work, just extract less
        assert "facts_extracted" in result

    @pytest.mark.asyncio
    async def test_process_node_deduplicates_facts(self, sample_state):
        """Should not return duplicate facts."""
        # Add duplicate entity
        sample_state["entities_found"].append(sample_state["entities_found"][0])

        result = await process_node(sample_state)

        # Check no exact duplicates
        statements = [f["statement"] for f in result["facts_extracted"]]
        assert len(statements) == len(set(statements))
EOF
```

**Step 3: Kør test - skal FEJLE (rød)**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/unit/test_process_node_llm.py -v
```

Expected: FAIL (extract_facts_with_llm does not exist)

**Step 4: Implementer process.py med rigtig LLM**

```bash
cat > /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/src/research_tool/agent/nodes/process.py << 'EOF'
"""Processing node - extract entities and facts from collected data using LLM."""

import hashlib
import json
from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState
from research_tool.services.llm.router import LLMRouter

logger = get_logger(__name__)

# Initialize LLM router
_llm_router: LLMRouter | None = None


def get_llm_router() -> LLMRouter:
    """Get or create the LLM router instance."""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router


FACT_EXTRACTION_PROMPT = """You are a fact extraction assistant. Extract factual statements from the provided content.

Rules:
1. Extract ONLY factual claims (not opinions or speculation)
2. Each fact should be a standalone statement
3. Include numerical data when present (percentages, dates, amounts)
4. Prioritize facts relevant to the query context
5. Rate confidence 0.0-1.0 based on how explicitly stated the fact is

Query context: {query_context}

Content to analyze:
{content}

Return JSON array of facts:
[
  {{"statement": "Factual statement here", "confidence": 0.8}},
  ...
]

Return ONLY the JSON array, no other text."""


async def extract_facts_with_llm(
    content: str,
    source_url: str,
    query_context: str
) -> list[dict[str, Any]]:
    """Extract facts from content using LLM.

    Args:
        content: Text content to extract facts from
        source_url: URL of the source for attribution
        query_context: Research query for relevance filtering

    Returns:
        List of fact dictionaries with statement, source, confidence
    """
    if not content or not content.strip():
        return []

    # Truncate content if too long (keep under 8000 chars for context)
    max_content_length = 8000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "..."

    router = get_llm_router()

    prompt = FACT_EXTRACTION_PROMPT.format(
        query_context=query_context,
        content=content
    )

    try:
        response = await router.complete(
            messages=[{"role": "user", "content": prompt}],
            model="local-fast",  # Use fast model for extraction
            temperature=0.1,  # Low temperature for factual extraction
            max_tokens=2000
        )

        # Parse JSON response
        response_text = response.strip()

        # Handle markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        facts_data = json.loads(response_text)

        # Normalize and add source
        facts = []
        for item in facts_data:
            if isinstance(item, dict) and "statement" in item:
                facts.append({
                    "statement": item["statement"],
                    "source": source_url,
                    "confidence": float(item.get("confidence", 0.5)),
                    "extracted_by": "llm"
                })

        logger.info(
            "facts_extracted_llm",
            source=source_url,
            count=len(facts)
        )

        return facts

    except json.JSONDecodeError as e:
        logger.warning(
            "fact_extraction_json_error",
            source=source_url,
            error=str(e)
        )
        return []
    except Exception as e:
        logger.error(
            "fact_extraction_failed",
            source=source_url,
            error=str(e)
        )
        return []


def deduplicate_facts(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate facts based on statement similarity.

    Args:
        facts: List of fact dictionaries

    Returns:
        Deduplicated list of facts
    """
    seen_hashes: set[str] = set()
    unique_facts = []

    for fact in facts:
        # Create hash of normalized statement
        statement = fact.get("statement", "").lower().strip()
        fact_hash = hashlib.md5(statement.encode()).hexdigest()

        if fact_hash not in seen_hashes:
            seen_hashes.add(fact_hash)
            unique_facts.append(fact)

    return unique_facts


async def process_node(state: ResearchState) -> dict[str, Any]:
    """Process collected data to extract entities and facts using LLM.

    This node:
    1. Iterates through collected entities
    2. Uses LLM to extract factual statements from full content
    3. Deduplicates extracted facts
    4. Returns enriched state with facts

    Args:
        state: Current research state

    Returns:
        dict: State updates with extracted facts
    """
    logger.info("process_node_start")

    entities = state.get("entities_found", [])
    query = state.get("refined_query", state.get("original_query", ""))

    all_facts: list[dict[str, Any]] = []

    for entity in entities:
        # Prefer full_content, fall back to snippet
        content = entity.get("full_content") or entity.get("snippet", "")

        if not content:
            continue

        source_url = entity.get("url", "unknown")

        # Extract facts using LLM
        facts = await extract_facts_with_llm(
            content=content,
            source_url=source_url,
            query_context=query
        )

        all_facts.extend(facts)

    # Deduplicate
    unique_facts = deduplicate_facts(all_facts)

    logger.info(
        "process_node_complete",
        entities_processed=len(entities),
        facts_extracted=len(unique_facts),
        duplicates_removed=len(all_facts) - len(unique_facts)
    )

    return {
        "facts_extracted": unique_facts,
        "current_phase": "process"
    }
EOF
```

**Step 5: Kør test igen - skal PASSE (grøn)**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/unit/test_process_node_llm.py -v
```

**Step 6: Kør linting**

```bash
uv run ruff check src/research_tool/agent/nodes/process.py
uv run python -m mypy src/research_tool/agent/nodes/process.py --ignore-missing-imports
```

**Step 7: Commit**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
git add backend/src/research_tool/agent/nodes/process.py backend/tests/unit/test_process_node_llm.py
git commit -m "feat(process): implement LLM-based fact extraction

- Replace fake fact generation with actual LLM extraction
- Use structured prompt for factual statement extraction
- Include confidence scoring from LLM
- Add deduplication based on statement hash
- Handle missing content gracefully
- Add comprehensive tests"
```

---

## Task 3.2: Implement analyze_node with Cross-Reference

**Problem:** Nuværende `analyze.py` er TOM SHELL - gør ingenting.

**Files:**
- Modify: `backend/src/research_tool/agent/nodes/analyze.py`
- Create: `backend/tests/unit/test_analyze_node.py`

**Step 1: Skriv TEST først**

```bash
cat > /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/tests/unit/test_analyze_node.py << 'EOF'
"""Tests for analyze node with cross-reference detection."""

import pytest

from research_tool.agent.nodes.analyze import (
    analyze_node,
    cross_reference_facts,
    detect_contradictions,
    calculate_fact_confidence,
)


@pytest.fixture
def facts_with_agreement():
    """Facts that agree with each other."""
    return [
        {
            "statement": "Global temperatures have risen 1.1°C since pre-industrial times",
            "source": "https://source1.com",
            "confidence": 0.8
        },
        {
            "statement": "Temperatures increased by 1.1 degrees Celsius above pre-industrial levels",
            "source": "https://source2.com",
            "confidence": 0.7
        },
        {
            "statement": "The planet has warmed approximately 1.1°C",
            "source": "https://source3.com",
            "confidence": 0.9
        }
    ]


@pytest.fixture
def facts_with_contradiction():
    """Facts that contradict each other."""
    return [
        {
            "statement": "The company was founded in 2010",
            "source": "https://source1.com",
            "confidence": 0.8
        },
        {
            "statement": "The company was established in 2015",
            "source": "https://source2.com",
            "confidence": 0.7
        }
    ]


@pytest.fixture
def sample_state(facts_with_agreement):
    """Sample research state."""
    return {
        "original_query": "climate change effects",
        "facts_extracted": facts_with_agreement,
        "entities_found": [],
    }


class TestCrossReferenceFacts:
    """Tests for fact cross-referencing."""

    @pytest.mark.asyncio
    async def test_finds_similar_facts(self, facts_with_agreement):
        """Should group similar facts together."""
        groups = await cross_reference_facts(facts_with_agreement)

        assert len(groups) >= 1
        # Should find that all 3 facts are about the same thing
        largest_group = max(groups, key=lambda g: len(g["facts"]))
        assert len(largest_group["facts"]) >= 2

    @pytest.mark.asyncio
    async def test_calculates_agreement_score(self, facts_with_agreement):
        """Should calculate agreement score for groups."""
        groups = await cross_reference_facts(facts_with_agreement)

        for group in groups:
            assert "agreement_score" in group
            assert 0 <= group["agreement_score"] <= 1


class TestDetectContradictions:
    """Tests for contradiction detection."""

    @pytest.mark.asyncio
    async def test_detects_year_contradiction(self, facts_with_contradiction):
        """Should detect contradicting years."""
        contradictions = await detect_contradictions(facts_with_contradiction)

        assert len(contradictions) >= 1
        assert any("2010" in str(c) or "2015" in str(c) for c in contradictions)

    @pytest.mark.asyncio
    async def test_no_false_positives(self, facts_with_agreement):
        """Should not flag agreeing facts as contradictions."""
        contradictions = await detect_contradictions(facts_with_agreement)

        # Agreeing facts should not be flagged
        assert len(contradictions) == 0


class TestCalculateFactConfidence:
    """Tests for confidence calculation."""

    def test_multi_source_increases_confidence(self, facts_with_agreement):
        """Facts from multiple sources should have higher confidence."""
        single_source_fact = facts_with_agreement[0]
        multi_source_fact = {
            **single_source_fact,
            "supporting_sources": ["source1.com", "source2.com", "source3.com"]
        }

        single_conf = calculate_fact_confidence(single_source_fact, [])
        multi_conf = calculate_fact_confidence(multi_source_fact, [])

        assert multi_conf > single_conf

    def test_contradiction_decreases_confidence(self, facts_with_contradiction):
        """Contradicted facts should have lower confidence."""
        fact = facts_with_contradiction[0]
        contradictions = [{"fact1": fact["statement"], "fact2": "conflicting"}]

        conf_without = calculate_fact_confidence(fact, [])
        conf_with = calculate_fact_confidence(fact, contradictions)

        assert conf_with < conf_without


class TestAnalyzeNode:
    """Tests for the analyze node."""

    @pytest.mark.asyncio
    async def test_analyze_node_returns_results(self, sample_state):
        """Should return analysis results."""
        result = await analyze_node(sample_state)

        assert "current_phase" in result
        assert result["current_phase"] == "analyze"
        assert "fact_groups" in result
        assert "contradictions" in result
        assert "confidence_scores" in result

    @pytest.mark.asyncio
    async def test_analyze_handles_empty_facts(self):
        """Should handle empty facts list."""
        state = {
            "original_query": "test",
            "facts_extracted": [],
            "entities_found": []
        }

        result = await analyze_node(state)
        assert result["current_phase"] == "analyze"
EOF
```

**Step 2: Kør test - skal FEJLE**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/unit/test_analyze_node.py -v
```

**Step 3: Implementer analyze.py**

```bash
cat > /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/src/research_tool/agent/nodes/analyze.py << 'EOF'
"""Analysis node - cross-verify facts, detect contradictions, score confidence."""

import re
from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState

logger = get_logger(__name__)


async def cross_reference_facts(
    facts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Group facts that discuss the same topic/claim.

    Uses text similarity to find facts making similar claims,
    which can then be used to boost confidence.

    Args:
        facts: List of extracted facts

    Returns:
        List of fact groups with agreement scores
    """
    if not facts:
        return []

    # Simple word-based similarity grouping
    groups: list[dict[str, Any]] = []
    used_indices: set[int] = set()

    for i, fact1 in enumerate(facts):
        if i in used_indices:
            continue

        group_facts = [fact1]
        statement1 = fact1.get("statement", "").lower()
        words1 = set(re.findall(r'\b\w+\b', statement1))

        for j, fact2 in enumerate(facts[i + 1:], start=i + 1):
            if j in used_indices:
                continue

            statement2 = fact2.get("statement", "").lower()
            words2 = set(re.findall(r'\b\w+\b', statement2))

            # Calculate Jaccard similarity
            if words1 and words2:
                intersection = len(words1 & words2)
                union = len(words1 | words2)
                similarity = intersection / union

                # Group if similarity > 0.4
                if similarity > 0.4:
                    group_facts.append(fact2)
                    used_indices.add(j)

        used_indices.add(i)

        # Calculate agreement score based on source diversity
        unique_sources = set(f.get("source", "") for f in group_facts)
        agreement_score = min(1.0, len(unique_sources) / 3)  # 3+ sources = 1.0

        groups.append({
            "facts": group_facts,
            "fact_count": len(group_facts),
            "unique_sources": list(unique_sources),
            "agreement_score": agreement_score
        })

    return groups


async def detect_contradictions(
    facts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Detect contradicting facts.

    Looks for facts that make conflicting claims about:
    - Dates/years
    - Numbers/amounts
    - Boolean states (is/is not)

    Args:
        facts: List of extracted facts

    Returns:
        List of contradiction pairs with details
    """
    contradictions: list[dict[str, Any]] = []

    # Patterns for extractable values
    year_pattern = r'\b(19|20)\d{2}\b'
    number_pattern = r'\b\d+(?:\.\d+)?(?:%|billion|million|thousand)?\b'

    for i, fact1 in enumerate(facts):
        stmt1 = fact1.get("statement", "")

        for fact2 in facts[i + 1:]:
            # Skip same source
            if fact1.get("source") == fact2.get("source"):
                continue

            stmt2 = fact2.get("statement", "")

            # Check for year contradictions
            years1 = set(re.findall(year_pattern, stmt1))
            years2 = set(re.findall(year_pattern, stmt2))

            if years1 and years2 and years1 != years2:
                # Check if statements are about similar topics
                if _statements_related(stmt1, stmt2):
                    contradictions.append({
                        "fact1": stmt1,
                        "fact1_source": fact1.get("source"),
                        "fact2": stmt2,
                        "fact2_source": fact2.get("source"),
                        "type": "year_conflict",
                        "values": {"fact1": list(years1), "fact2": list(years2)}
                    })
                    continue

            # Check for number contradictions
            nums1 = re.findall(number_pattern, stmt1)
            nums2 = re.findall(number_pattern, stmt2)

            if nums1 and nums2 and _statements_related(stmt1, stmt2):
                # Compare first number found
                try:
                    n1 = float(re.sub(r'[^\d.]', '', nums1[0]))
                    n2 = float(re.sub(r'[^\d.]', '', nums2[0]))

                    # Significant difference (>20%)
                    if max(n1, n2) > 0 and abs(n1 - n2) / max(n1, n2) > 0.2:
                        contradictions.append({
                            "fact1": stmt1,
                            "fact1_source": fact1.get("source"),
                            "fact2": stmt2,
                            "fact2_source": fact2.get("source"),
                            "type": "number_conflict",
                            "values": {"fact1": n1, "fact2": n2}
                        })
                except (ValueError, IndexError):
                    pass

    logger.info("contradictions_detected", count=len(contradictions))
    return contradictions


def _statements_related(stmt1: str, stmt2: str) -> bool:
    """Check if two statements are about the same topic.

    Args:
        stmt1: First statement
        stmt2: Second statement

    Returns:
        True if statements appear related
    """
    # Common words to exclude
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
        "to", "for", "of", "and", "or", "but", "by", "from", "has", "have"
    }

    words1 = {w.lower() for w in re.findall(r'\b\w+\b', stmt1) if w.lower() not in stop_words and len(w) > 2}
    words2 = {w.lower() for w in re.findall(r'\b\w+\b', stmt2) if w.lower() not in stop_words and len(w) > 2}

    if not words1 or not words2:
        return False

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union > 0.3 if union > 0 else False


def calculate_fact_confidence(
    fact: dict[str, Any],
    contradictions: list[dict[str, Any]]
) -> float:
    """Calculate final confidence score for a fact.

    Factors:
    - Original extraction confidence
    - Number of supporting sources
    - Presence of contradictions

    Args:
        fact: Fact dictionary
        contradictions: List of detected contradictions

    Returns:
        Confidence score 0.0-1.0
    """
    base_confidence = fact.get("confidence", 0.5)

    # Boost for multiple sources
    supporting = fact.get("supporting_sources", [])
    source_boost = min(0.3, len(supporting) * 0.1)

    # Penalty for contradictions
    statement = fact.get("statement", "")
    contradiction_penalty = 0.0
    for c in contradictions:
        if statement in (c.get("fact1", ""), c.get("fact2", "")):
            contradiction_penalty = 0.3
            break

    final = base_confidence + source_boost - contradiction_penalty
    return max(0.1, min(1.0, final))


async def analyze_node(state: ResearchState) -> dict[str, Any]:
    """Analyze facts for cross-verification and confidence scoring.

    This node:
    1. Cross-references facts to find agreement
    2. Detects contradictions between facts
    3. Calculates final confidence scores
    4. Groups related facts together

    Args:
        state: Current research state

    Returns:
        dict: State updates with analysis results
    """
    logger.info("analyze_node_start")

    facts = state.get("facts_extracted", [])

    if not facts:
        logger.info("analyze_node_no_facts")
        return {
            "current_phase": "analyze",
            "fact_groups": [],
            "contradictions": [],
            "confidence_scores": {}
        }

    # Cross-reference facts
    fact_groups = await cross_reference_facts(facts)

    # Detect contradictions
    contradictions = await detect_contradictions(facts)

    # Calculate confidence scores
    confidence_scores = {}
    for i, fact in enumerate(facts):
        confidence_scores[f"fact_{i}"] = calculate_fact_confidence(fact, contradictions)

    # Update facts with group info
    for group in fact_groups:
        sources = group["unique_sources"]
        for fact in group["facts"]:
            fact["supporting_sources"] = sources
            fact["group_agreement"] = group["agreement_score"]

    logger.info(
        "analyze_node_complete",
        facts_analyzed=len(facts),
        groups_found=len(fact_groups),
        contradictions_found=len(contradictions)
    )

    return {
        "current_phase": "analyze",
        "fact_groups": fact_groups,
        "contradictions": contradictions,
        "confidence_scores": confidence_scores
    }
EOF
```

**Step 4: Kør test - skal PASSE**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/unit/test_analyze_node.py -v
```

**Step 5: Kør linting**

```bash
uv run ruff check src/research_tool/agent/nodes/analyze.py
uv run python -m mypy src/research_tool/agent/nodes/analyze.py --ignore-missing-imports
```

**Step 6: Commit**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
git add backend/src/research_tool/agent/nodes/analyze.py backend/tests/unit/test_analyze_node.py
git commit -m "feat(analyze): implement cross-reference and contradiction detection

- Add fact grouping by text similarity
- Detect year and number contradictions
- Calculate confidence with multi-source boost
- Penalize contradicted facts
- Add comprehensive test suite"
```

---

## Task 3.3: Implement synthesize_node with LLM Report Generation

**Problem:** Nuværende `synthesize.py` genererer FAKE rapport uden LLM.

**Files:**
- Modify: `backend/src/research_tool/agent/nodes/synthesize.py`
- Create: `backend/tests/unit/test_synthesize_node.py`

**Step 1: Skriv TEST først**

```bash
cat > /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/tests/unit/test_synthesize_node.py << 'EOF'
"""Tests for synthesize node with LLM report generation."""

import pytest

from research_tool.agent.nodes.synthesize import (
    generate_executive_summary,
    generate_limitations,
    synthesize_node,
)


@pytest.fixture
def sample_state():
    """Sample research state with analyzed facts."""
    return {
        "original_query": "What are the effects of climate change on agriculture?",
        "refined_query": "climate change agricultural impact crop yields",
        "domain": "academic",
        "facts_extracted": [
            {
                "statement": "Wheat yields decreased 5.5% since 1980",
                "source": "https://nature.com/article1",
                "confidence": 0.85,
                "supporting_sources": ["nature.com", "science.org"]
            },
            {
                "statement": "Temperatures rose 1.1°C above pre-industrial levels",
                "source": "https://ipcc.ch/report",
                "confidence": 0.95,
                "supporting_sources": ["ipcc.ch", "nasa.gov", "noaa.gov"]
            }
        ],
        "fact_groups": [
            {"facts": [], "agreement_score": 0.8}
        ],
        "contradictions": [],
        "sources_queried": ["semantic_scholar", "pubmed", "arxiv"],
        "entities_found": [
            {"url": "https://nature.com/article1", "title": "Climate Impact Study"}
        ],
        "saturation_metrics": {"new_entity_ratio": 0.02},
        "stop_reason": "Saturation reached"
    }


class TestGenerateExecutiveSummary:
    """Tests for executive summary generation."""

    @pytest.mark.asyncio
    async def test_generates_summary(self, sample_state):
        """Should generate a coherent summary."""
        summary = await generate_executive_summary(
            query=sample_state["original_query"],
            facts=sample_state["facts_extracted"],
            domain=sample_state["domain"]
        )

        assert len(summary) > 50
        assert isinstance(summary, str)

    @pytest.mark.asyncio
    async def test_summary_references_query(self, sample_state):
        """Summary should be relevant to query."""
        summary = await generate_executive_summary(
            query=sample_state["original_query"],
            facts=sample_state["facts_extracted"],
            domain=sample_state["domain"]
        )

        # Should mention key topics
        summary_lower = summary.lower()
        assert any(word in summary_lower for word in ["climate", "agriculture", "crop"])


class TestGenerateLimitations:
    """Tests for limitations generation."""

    def test_identifies_source_limitations(self, sample_state):
        """Should identify source coverage limitations."""
        limitations = generate_limitations(
            sources_queried=sample_state["sources_queried"],
            contradictions=sample_state["contradictions"],
            domain=sample_state["domain"]
        )

        assert len(limitations) > 0
        assert all(isinstance(l, str) for l in limitations)

    def test_notes_contradictions(self):
        """Should note when contradictions exist."""
        limitations = generate_limitations(
            sources_queried=["pubmed"],
            contradictions=[{"type": "year_conflict"}],
            domain="medical"
        )

        assert any("contradict" in l.lower() for l in limitations)


class TestSynthesizeNode:
    """Tests for the synthesize node."""

    @pytest.mark.asyncio
    async def test_synthesize_returns_report(self, sample_state):
        """Should return complete report structure."""
        result = await synthesize_node(sample_state)

        assert "final_report" in result
        assert "current_phase" in result
        assert result["current_phase"] == "synthesize"

        report = result["final_report"]
        assert "query" in report
        assert "summary" in report
        assert "findings" in report
        assert "sources" in report
        assert "limitations" in report
        assert "methodology" in report

    @pytest.mark.asyncio
    async def test_synthesize_handles_empty(self):
        """Should handle empty facts gracefully."""
        state = {
            "original_query": "test query",
            "facts_extracted": [],
            "sources_queried": [],
            "entities_found": [],
            "contradictions": []
        }

        result = await synthesize_node(state)

        assert "final_report" in result
        report = result["final_report"]
        assert "No facts were extracted" in report["summary"] or len(report["findings"]) == 0
EOF
```

**Step 2: Kør test - skal FEJLE**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/unit/test_synthesize_node.py -v
```

**Step 3: Implementer synthesize.py**

```bash
cat > /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/src/research_tool/agent/nodes/synthesize.py << 'EOF'
"""Synthesis node - generate final research report using LLM."""

from datetime import datetime
from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState
from research_tool.services.llm.router import LLMRouter

logger = get_logger(__name__)

# Initialize LLM router
_llm_router: LLMRouter | None = None


def get_llm_router() -> LLMRouter:
    """Get or create the LLM router instance."""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router


SUMMARY_PROMPT = """You are a research analyst writing an executive summary.

Research Question: {query}
Domain: {domain}

Key Findings:
{findings}

Write a concise executive summary (2-3 paragraphs) that:
1. Directly answers the research question
2. Highlights the most important findings
3. Notes the confidence level based on source agreement
4. Is written in a professional, objective tone

Write ONLY the summary, no headers or labels."""


async def generate_executive_summary(
    query: str,
    facts: list[dict[str, Any]],
    domain: str
) -> str:
    """Generate executive summary using LLM.

    Args:
        query: Original research question
        facts: Extracted and verified facts
        domain: Research domain

    Returns:
        Executive summary text
    """
    if not facts:
        return "No facts were extracted from the sources. The research query may need refinement or additional sources may be required."

    # Format findings for prompt
    findings_text = "\n".join([
        f"- {f['statement']} (confidence: {f.get('confidence', 0.5):.0%}, sources: {len(f.get('supporting_sources', [f.get('source', 'unknown')]))})"
        for f in facts[:10]  # Top 10 facts
    ])

    router = get_llm_router()

    prompt = SUMMARY_PROMPT.format(
        query=query,
        domain=domain,
        findings=findings_text
    )

    try:
        summary = await router.complete(
            messages=[{"role": "user", "content": prompt}],
            model="cloud-best",  # Use best model for synthesis
            temperature=0.3,
            max_tokens=500
        )
        return summary.strip()

    except Exception as e:
        logger.error("summary_generation_failed", error=str(e))
        # Fallback to simple summary
        return f"Research on '{query}' found {len(facts)} key findings. The highest confidence findings include: {facts[0]['statement'] if facts else 'None'}."


def generate_limitations(
    sources_queried: list[str],
    contradictions: list[dict[str, Any]],
    domain: str
) -> list[str]:
    """Generate list of research limitations.

    Args:
        sources_queried: List of sources that were searched
        contradictions: Detected contradictions
        domain: Research domain

    Returns:
        List of limitation statements
    """
    limitations = []

    # Source coverage
    all_sources = {"pubmed", "arxiv", "semantic_scholar", "tavily", "brave"}
    missing = all_sources - set(sources_queried)
    if missing:
        limitations.append(
            f"Not all sources were queried. Missing: {', '.join(missing)}"
        )

    # Contradictions
    if contradictions:
        limitations.append(
            f"Found {len(contradictions)} contradicting claims between sources. "
            "Manual verification recommended."
        )

    # Domain-specific
    if domain == "medical":
        limitations.append(
            "Medical information should be verified by healthcare professionals. "
            "This research is not a substitute for medical advice."
        )
    elif domain == "academic":
        limitations.append(
            "Academic claims should be verified against primary sources. "
            "Citation analysis was limited to available metadata."
        )

    # General
    limitations.append(
        "This research represents a snapshot in time. "
        "Information may have changed since sources were published."
    )

    return limitations


async def synthesize_node(state: ResearchState) -> dict[str, Any]:
    """Synthesize research findings into final report.

    This node:
    1. Generates executive summary using LLM
    2. Organizes findings by confidence
    3. Documents methodology and limitations
    4. Creates structured report

    Anti-pattern prevention:
    - Include what was NOT found (Anti-Pattern #11)
    - Explain stopping rationale (Anti-Pattern #12)

    Args:
        state: Current research state

    Returns:
        dict: State updates with final report
    """
    logger.info("synthesize_node_start")

    query = state.get("refined_query", state.get("original_query", "Unknown query"))
    domain = state.get("domain", "general")
    facts = state.get("facts_extracted", [])
    sources_queried = state.get("sources_queried", [])
    entities = state.get("entities_found", [])
    contradictions = state.get("contradictions", [])
    saturation = state.get("saturation_metrics", {})
    stop_reason = state.get("stop_reason", "Unknown")

    # Generate executive summary
    summary = await generate_executive_summary(query, facts, domain)

    # Sort facts by confidence
    sorted_facts = sorted(
        facts,
        key=lambda f: f.get("confidence", 0),
        reverse=True
    )

    # Generate limitations
    limitations = generate_limitations(sources_queried, contradictions, domain)

    # Build report
    report = {
        "query": query,
        "domain": domain,
        "generated_at": datetime.now().isoformat(),

        # Summary
        "summary": summary,

        # Findings (sorted by confidence)
        "findings": [
            {
                "statement": f["statement"],
                "confidence": f.get("confidence", 0.5),
                "source": f.get("source", "Unknown"),
                "supporting_sources": f.get("supporting_sources", [])
            }
            for f in sorted_facts[:20]
        ],

        # Sources
        "sources": [
            {
                "url": e.get("url", ""),
                "title": e.get("title", "Unknown"),
                "type": e.get("source_name", "web")
            }
            for e in entities[:30]
        ],

        # Methodology
        "methodology": {
            "sources_queried": sources_queried,
            "entities_found": len(entities),
            "facts_extracted": len(facts),
            "saturation_metrics": saturation,
            "stop_reason": stop_reason
        },

        # Limitations and gaps
        "limitations": limitations,
        "contradictions_found": len(contradictions),

        # Confidence metrics
        "overall_confidence": (
            sum(f.get("confidence", 0.5) for f in facts) / len(facts)
            if facts else 0.0
        )
    }

    logger.info(
        "synthesize_node_complete",
        findings_count=len(report["findings"]),
        sources_count=len(report["sources"]),
        overall_confidence=report["overall_confidence"]
    )

    return {
        "final_report": report,
        "current_phase": "synthesize"
    }
EOF
```

**Step 4: Kør test - skal PASSE**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/unit/test_synthesize_node.py -v
```

**Step 5: Kør linting**

```bash
uv run ruff check src/research_tool/agent/nodes/synthesize.py
uv run python -m mypy src/research_tool/agent/nodes/synthesize.py --ignore-missing-imports
```

**Step 6: Commit**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
git add backend/src/research_tool/agent/nodes/synthesize.py backend/tests/unit/test_synthesize_node.py
git commit -m "feat(synthesize): implement LLM-based report generation

- Generate executive summary with Claude
- Sort findings by confidence score
- Document methodology and limitations
- Include contradiction warnings
- Calculate overall confidence
- Add domain-specific limitations"
```

---

# FASE 4: PRODUCTION HARDENING

## Task 4.1: Create E2E Test Suite

**Files:**
- Create: `backend/tests/e2e/test_research_workflow.py`

**Step 1: Opret E2E test**

```bash
mkdir -p /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/tests/e2e
cat > /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend/tests/e2e/test_research_workflow.py << 'EOF'
"""End-to-end tests for complete research workflow."""

import pytest
from httpx import AsyncClient

from research_tool.main import app


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_basic_health(self, client):
        """Basic health check should return healthy."""
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_detailed_health(self, client):
        """Detailed health should return component status."""
        response = await client.get("/api/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "components" in data
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_config_status(self, client):
        """Config endpoint should return safe config."""
        response = await client.get("/api/health/config")
        assert response.status_code == 200
        data = response.json()
        assert "features" in data
        # Should not expose actual keys
        if data["config"].get("anthropic_api_key"):
            assert data["config"]["anthropic_api_key"] == "***"


class TestResearchWorkflow:
    """Test research workflow endpoints."""

    @pytest.mark.asyncio
    async def test_start_research(self, client):
        """Should start research session."""
        response = await client.post(
            "/api/research/start",
            json={
                "query": "What is machine learning?",
                "privacy_mode": "cloud_allowed"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "started"

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, client):
        """Should return 404 for unknown session."""
        response = await client.get("/api/research/nonexistent-id/status")
        assert response.status_code == 404


class TestExportEndpoints:
    """Test export functionality."""

    @pytest.mark.asyncio
    async def test_export_formats(self, client):
        """Should list available export formats."""
        response = await client.get("/api/export/formats")
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert "markdown" in data["formats"]
        assert "pdf" in data["formats"]
EOF
```

**Step 2: Kør E2E tests**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/e2e/ -v
```

**Step 3: Commit**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT
git add backend/tests/e2e/
git commit -m "test(e2e): add end-to-end test suite for research workflow

- Test health endpoints
- Test research start and status
- Test export format listing
- Verify API contracts"
```

---

## Task 4.2: Verificer ALLE Tests Passerer

**Step 1: Kør komplet test suite**

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/ -v --tb=short | tee test_results.txt
```

**Step 2: Kør linting**

```bash
uv run ruff check src/ tests/
```

**Step 3: Kør type checking**

```bash
uv run python -m mypy src/ --ignore-missing-imports
```

**Step 4: Verificer alt er clean**

Expected output:
- All tests pass
- `All checks passed!` fra ruff
- `Success: no issues found` fra mypy

---

# FINAL VERIFICATION CHECKLIST

Før planen er komplet, verificer:

```bash
# 1. Backend starter
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run uvicorn src.research_tool.main:app --host 127.0.0.1 --port 8000 &
sleep 5

# 2. Health check virker
curl http://localhost:8000/api/health/detailed | python -m json.tool

# 3. Rebuild GUI
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/gui/ResearchTool
swift build -c release

# 4. Stop backend
kill %1

# 5. Final test run
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/ -q
uv run ruff check src/
uv run python -m mypy src/ --ignore-missing-imports

# 6. Git status clean
git status
```

---

# PLAN KOMPLET

**Total Tasks:** 15 hovedopgaver
**Estimeret commits:** 15-20
**Faser:** 4

**Efter denne plan er implementeret:**
- ✅ Backend path resolution virker
- ✅ Config validation ved startup
- ✅ Deep health checks
- ✅ Circuit breaker integreret i alle providers
- ✅ process_node bruger LLM til fact extraction
- ✅ analyze_node laver cross-reference og contradiction detection
- ✅ synthesize_node genererer ægte rapport med LLM
- ✅ E2E test suite verificerer workflow
- ✅ Alle tests passer

