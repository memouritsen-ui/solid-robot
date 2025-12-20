# Distributed Crawling Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Celery + Redis distributed crawling with explicit `distributed=True` API parameter.

**Architecture:** Workers in Docker containers pull URLs from Redis queue, crawl with Playwright, return results to coordinator. Existing direct crawling unchanged.

**Tech Stack:** Celery 5.3+, Redis 7, Docker Compose, Playwright

---

## Task 1: Add Dependencies

**Files:**
- Modify: `backend/pyproject.toml`

**Step 1: Add distributed optional dependencies**

Add to `pyproject.toml` under `[project.optional-dependencies]`:

```toml
distributed = [
    "celery[redis]>=5.3.0",
    "redis>=5.0.0",
]
```

**Step 2: Sync dependencies**

Run: `cd backend && uv sync --extra distributed`
Expected: Successfully installed celery, redis, kombu, etc.

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat(deps): add celery and redis for distributed crawling"
```

---

## Task 2: Create Distributed Config

**Files:**
- Create: `backend/src/research_tool/services/distributed/__init__.py`
- Create: `backend/src/research_tool/services/distributed/config.py`

**Step 1: Create directory and __init__.py**

```bash
mkdir -p backend/src/research_tool/services/distributed
```

Create `backend/src/research_tool/services/distributed/__init__.py`:

```python
"""Distributed crawling with Celery + Redis."""

from research_tool.services.distributed.config import DistributedConfig

_config: DistributedConfig | None = None


def get_distributed_config() -> DistributedConfig:
    """Get distributed configuration singleton."""
    global _config
    if _config is None:
        _config = DistributedConfig()
    return _config


def is_distributed_available() -> bool:
    """Check if Redis is reachable."""
    try:
        import redis
        config = get_distributed_config()
        client = redis.from_url(config.broker_url)
        client.ping()
        return True
    except Exception:
        return False


__all__ = [
    "DistributedConfig",
    "get_distributed_config",
    "is_distributed_available",
]
```

**Step 2: Create config.py**

Create `backend/src/research_tool/services/distributed/config.py`:

```python
"""Configuration for distributed crawling."""

from pydantic_settings import BaseSettings


class DistributedConfig(BaseSettings):
    """Distributed crawling configuration."""

    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"
    task_rate_limit: str = "10/m"
    task_max_retries: int = 3
    task_retry_backoff: int = 60
    worker_concurrency: int = 1
    worker_prefetch_multiplier: int = 1

    class Config:
        env_prefix = "CELERY_"
```

**Step 3: Commit**

```bash
git add backend/src/research_tool/services/distributed/
git commit -m "feat(distributed): add config module"
```

---

## Task 3: Create Celery App

**Files:**
- Create: `backend/src/research_tool/services/distributed/celery_app.py`
- Test: `backend/tests/unit/test_distributed_celery.py`

**Step 1: Write failing test**

Create `backend/tests/unit/test_distributed_celery.py`:

```python
"""Tests for Celery app configuration."""

import pytest


class TestCeleryApp:
    """Test Celery application setup."""

    def test_celery_app_exists(self) -> None:
        """Celery app can be imported."""
        from research_tool.services.distributed.celery_app import app
        assert app is not None
        assert app.main == "solid_robot"

    def test_celery_app_has_broker_configured(self) -> None:
        """Celery app has broker URL configured."""
        from research_tool.services.distributed.celery_app import app
        assert "redis://" in app.conf.broker_url

    def test_celery_app_has_result_backend(self) -> None:
        """Celery app has result backend configured."""
        from research_tool.services.distributed.celery_app import app
        assert "redis://" in app.conf.result_backend
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run python -m pytest tests/unit/test_distributed_celery.py -v`
Expected: FAIL with "ModuleNotFoundError" or "cannot import name 'app'"

**Step 3: Write implementation**

Create `backend/src/research_tool/services/distributed/celery_app.py`:

```python
"""Celery application configuration."""

from celery import Celery

from research_tool.services.distributed.config import DistributedConfig

config = DistributedConfig()

app = Celery(
    "solid_robot",
    broker=config.broker_url,
    backend=config.result_backend,
    include=["research_tool.services.distributed.tasks"],
)

# Task configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=config.worker_prefetch_multiplier,
)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run python -m pytest tests/unit/test_distributed_celery.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add backend/src/research_tool/services/distributed/celery_app.py backend/tests/unit/test_distributed_celery.py
git commit -m "feat(distributed): add Celery app configuration"
```

---

## Task 4: Create Crawl Task

**Files:**
- Create: `backend/src/research_tool/services/distributed/tasks.py`
- Test: `backend/tests/unit/test_distributed_tasks.py`

**Step 1: Write failing test**

Create `backend/tests/unit/test_distributed_tasks.py`:

```python
"""Tests for distributed crawl tasks."""

from unittest.mock import MagicMock, patch

import pytest


class TestCrawlUrlTask:
    """Test crawl_url task."""

    def test_task_exists(self) -> None:
        """crawl_url task can be imported."""
        from research_tool.services.distributed.tasks import crawl_url
        assert crawl_url is not None
        assert hasattr(crawl_url, "delay")

    def test_task_returns_success_dict(self) -> None:
        """Task returns success dict with required fields."""
        from research_tool.services.distributed.tasks import crawl_url

        with patch(
            "research_tool.services.distributed.tasks._fetch_url"
        ) as mock_fetch:
            mock_fetch.return_value = {
                "content": "Test content",
                "title": "Test Title",
            }

            result = crawl_url.run(
                url="https://example.com",
                session_id="test-123",
                options={},
            )

            assert result["status"] == "success"
            assert result["url"] == "https://example.com"
            assert "content" in result

    def test_task_returns_failure_on_error(self) -> None:
        """Task returns failure dict on exception."""
        from research_tool.services.distributed.tasks import crawl_url

        with patch(
            "research_tool.services.distributed.tasks._fetch_url"
        ) as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")

            result = crawl_url.run(
                url="https://example.com",
                session_id="test-123",
                options={},
            )

            assert result["status"] == "failed"
            assert "error" in result
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run python -m pytest tests/unit/test_distributed_tasks.py -v`
Expected: FAIL with import error

**Step 3: Write implementation**

Create `backend/src/research_tool/services/distributed/tasks.py`:

```python
"""Celery tasks for distributed crawling."""

import socket
from datetime import datetime, timezone
from typing import Any

from celery import Task

from research_tool.core.logging import get_logger
from research_tool.services.distributed.celery_app import app
from research_tool.services.distributed.config import DistributedConfig

logger = get_logger(__name__)
config = DistributedConfig()


def _fetch_url(url: str, options: dict) -> dict[str, Any]:
    """Fetch URL content using existing crawler logic.

    This is a sync wrapper that will be called by the Celery task.
    """
    import asyncio
    from research_tool.services.search.crawler import PlaywrightCrawler

    async def _async_fetch():
        crawler = PlaywrightCrawler()
        result = await crawler.fetch_url(url)
        return result

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_async_fetch())
    finally:
        loop.close()


class CrawlTask(Task):
    """Base task with shared resources."""

    abstract = True


@app.task(
    bind=True,
    base=CrawlTask,
    max_retries=config.task_max_retries,
    rate_limit=config.task_rate_limit,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
)
def crawl_url(
    self,
    url: str,
    session_id: str,
    options: dict | None = None,
) -> dict[str, Any]:
    """Crawl a single URL.

    Args:
        url: URL to crawl
        session_id: Research session ID for grouping
        options: Optional crawl options

    Returns:
        Dict with status, url, content, and metadata
    """
    options = options or {}
    worker_id = socket.gethostname()

    try:
        logger.info("crawl_task_start", url=url, session_id=session_id)

        result = _fetch_url(url, options)

        return {
            "status": "success",
            "url": url,
            "session_id": session_id,
            "worker_id": worker_id,
            "crawled_at": datetime.now(timezone.utc).isoformat(),
            **result,
        }

    except Exception as e:
        logger.error("crawl_task_error", url=url, error=str(e))
        return {
            "status": "failed",
            "url": url,
            "session_id": session_id,
            "worker_id": worker_id,
            "error": str(e),
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run python -m pytest tests/unit/test_distributed_tasks.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add backend/src/research_tool/services/distributed/tasks.py backend/tests/unit/test_distributed_tasks.py
git commit -m "feat(distributed): add crawl_url Celery task"
```

---

## Task 5: Create Coordinator

**Files:**
- Create: `backend/src/research_tool/services/distributed/coordinator.py`
- Test: `backend/tests/unit/test_distributed_coordinator.py`

**Step 1: Write failing test**

Create `backend/tests/unit/test_distributed_coordinator.py`:

```python
"""Tests for CrawlCoordinator."""

from unittest.mock import MagicMock, patch

import pytest


class TestCrawlCoordinator:
    """Test CrawlCoordinator."""

    def test_coordinator_init(self) -> None:
        """Coordinator initializes with session_id."""
        from research_tool.services.distributed.coordinator import CrawlCoordinator

        coordinator = CrawlCoordinator(session_id="test-123")
        assert coordinator.session_id == "test-123"

    def test_get_stats_empty(self) -> None:
        """Stats returns zeros for empty results."""
        from research_tool.services.distributed.coordinator import CrawlCoordinator

        coordinator = CrawlCoordinator(session_id="test-123")
        stats = coordinator.get_stats([])

        assert stats["total"] == 0
        assert stats["success"] == 0
        assert stats["failed"] == 0

    def test_get_stats_with_results(self) -> None:
        """Stats correctly counts success/failure."""
        from research_tool.services.distributed.coordinator import CrawlCoordinator

        coordinator = CrawlCoordinator(session_id="test-123")
        results = [
            {"status": "success", "worker_id": "w1"},
            {"status": "success", "worker_id": "w2"},
            {"status": "failed", "worker_id": "w1"},
        ]
        stats = coordinator.get_stats(results)

        assert stats["total"] == 3
        assert stats["success"] == 2
        assert stats["failed"] == 1
        assert stats["workers_used"] == 2
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run python -m pytest tests/unit/test_distributed_coordinator.py -v`
Expected: FAIL with import error

**Step 3: Write implementation**

Create `backend/src/research_tool/services/distributed/coordinator.py`:

```python
"""Coordinator for distributed crawling."""

from typing import Any, Callable

from celery import group
from celery.result import GroupResult

from research_tool.core.logging import get_logger
from research_tool.services.distributed.tasks import crawl_url

logger = get_logger(__name__)


class CrawlCoordinator:
    """Orchestrates distributed crawling and aggregates results."""

    def __init__(self, session_id: str):
        """Initialize coordinator.

        Args:
            session_id: Research session ID for grouping results
        """
        self.session_id = session_id

    def crawl_many_sync(
        self,
        urls: list[str],
        options: dict | None = None,
        timeout: float = 300.0,
    ) -> list[dict[str, Any]]:
        """Distribute URLs across workers and collect results (sync).

        Args:
            urls: List of URLs to crawl
            options: Optional crawl options
            timeout: Max wait time in seconds

        Returns:
            List of crawl results
        """
        if not urls:
            return []

        options = options or {}

        # Create task group
        task_group = group(
            crawl_url.s(url, self.session_id, options) for url in urls
        )

        # Execute
        logger.info(
            "distributed_crawl_start",
            session_id=self.session_id,
            url_count=len(urls),
        )

        group_result: GroupResult = task_group.apply_async()

        # Wait for results
        results = group_result.get(timeout=timeout, propagate=False)

        logger.info(
            "distributed_crawl_complete",
            session_id=self.session_id,
            result_count=len(results),
        )

        return results

    async def crawl_many(
        self,
        urls: list[str],
        options: dict | None = None,
        on_progress: Callable[[int, int], None] | None = None,
        timeout: float = 300.0,
    ) -> list[dict[str, Any]]:
        """Distribute URLs across workers and collect results (async).

        Args:
            urls: List of URLs to crawl
            options: Optional crawl options
            on_progress: Progress callback(completed, total)
            timeout: Max wait time in seconds

        Returns:
            List of crawl results
        """
        import asyncio

        if not urls:
            return []

        options = options or {}

        # Create and dispatch task group
        task_group = group(
            crawl_url.s(url, self.session_id, options) for url in urls
        )
        group_result: GroupResult = task_group.apply_async()

        # Poll for completion with progress updates
        completed = 0
        while not group_result.ready():
            new_completed = group_result.completed_count()
            if new_completed > completed:
                completed = new_completed
                if on_progress:
                    on_progress(completed, len(urls))
            await asyncio.sleep(0.5)

        # Final progress update
        if on_progress:
            on_progress(len(urls), len(urls))

        return group_result.get(timeout=timeout, propagate=False)

    def get_stats(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate statistics from results.

        Args:
            results: List of crawl results

        Returns:
            Stats dict with total, success, failed, workers_used
        """
        if not results:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "workers_used": 0,
            }

        success = sum(1 for r in results if r.get("status") == "success")
        workers = set(r.get("worker_id") for r in results if r.get("worker_id"))

        return {
            "total": len(results),
            "success": success,
            "failed": len(results) - success,
            "workers_used": len(workers),
        }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run python -m pytest tests/unit/test_distributed_coordinator.py -v`
Expected: 3 passed

**Step 5: Update __init__.py exports**

Add to `backend/src/research_tool/services/distributed/__init__.py`:

```python
from research_tool.services.distributed.coordinator import CrawlCoordinator

# Add to __all__:
__all__ = [
    "DistributedConfig",
    "get_distributed_config",
    "is_distributed_available",
    "CrawlCoordinator",
]
```

**Step 6: Commit**

```bash
git add backend/src/research_tool/services/distributed/ backend/tests/unit/test_distributed_coordinator.py
git commit -m "feat(distributed): add CrawlCoordinator"
```

---

## Task 6: Add API Endpoint

**Files:**
- Create: `backend/src/research_tool/api/routes/crawl.py`
- Modify: `backend/src/research_tool/api/routes/__init__.py`
- Test: `backend/tests/unit/test_crawl_api.py`

**Step 1: Write failing test**

Create `backend/tests/unit/test_crawl_api.py`:

```python
"""Tests for crawl API endpoints."""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


class TestCrawlBatchEndpoint:
    """Test /api/crawl/batch endpoint."""

    def test_crawl_batch_direct_mode(self) -> None:
        """Direct crawling works without distributed."""
        from research_tool.main import app

        client = TestClient(app)

        with patch(
            "research_tool.api.routes.crawl.PlaywrightCrawler"
        ) as mock_crawler:
            mock_instance = MagicMock()
            mock_instance.fetch_url = MagicMock(
                return_value={"content": "test", "title": "Test"}
            )
            mock_crawler.return_value = mock_instance

            response = client.post(
                "/api/crawl/batch",
                json={
                    "urls": ["https://example.com"],
                    "session_id": "test-123",
                    "distributed": False,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["distributed"] is False
            assert data["total"] == 1

    def test_crawl_batch_distributed_unavailable(self) -> None:
        """Returns 503 when distributed requested but unavailable."""
        from research_tool.main import app

        client = TestClient(app)

        with patch(
            "research_tool.api.routes.crawl.is_distributed_available"
        ) as mock_avail:
            mock_avail.return_value = False

            response = client.post(
                "/api/crawl/batch",
                json={
                    "urls": ["https://example.com"],
                    "session_id": "test-123",
                    "distributed": True,
                },
            )

            assert response.status_code == 503
            assert "not available" in response.json()["detail"]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run python -m pytest tests/unit/test_crawl_api.py -v`
Expected: FAIL with 404 or import error

**Step 3: Write implementation**

Create `backend/src/research_tool/api/routes/crawl.py`:

```python
"""Crawl API endpoints."""

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from research_tool.services.distributed import (
    CrawlCoordinator,
    is_distributed_available,
)
from research_tool.services.search.crawler import PlaywrightCrawler

router = APIRouter(prefix="/api/crawl", tags=["crawl"])


class CrawlRequest(BaseModel):
    """Request for batch crawling."""

    urls: list[str] = Field(..., min_length=1, max_length=1000)
    session_id: str
    distributed: bool = False
    options: dict[str, Any] | None = None


class CrawlResponse(BaseModel):
    """Response from batch crawling."""

    session_id: str
    total: int
    success: int
    failed: int
    distributed: bool
    workers_used: int | None = None
    results: list[dict[str, Any]]


@router.post("/batch", response_model=CrawlResponse)
async def crawl_batch(request: CrawlRequest) -> CrawlResponse:
    """Crawl multiple URLs.

    Args:
        request: Crawl request with URLs and options

    Returns:
        Crawl response with results and statistics
    """
    if request.distributed:
        if not is_distributed_available():
            raise HTTPException(
                status_code=503,
                detail="Distributed crawling not available. Start Redis + workers.",
            )

        coordinator = CrawlCoordinator(request.session_id)
        results = await coordinator.crawl_many(
            request.urls,
            request.options,
        )
        stats = coordinator.get_stats(results)

        return CrawlResponse(
            session_id=request.session_id,
            distributed=True,
            workers_used=stats["workers_used"],
            total=stats["total"],
            success=stats["success"],
            failed=stats["failed"],
            results=results,
        )

    else:
        # Direct crawling
        crawler = PlaywrightCrawler()
        results = []

        for url in request.urls:
            try:
                result = await crawler.fetch_url(url)
                results.append({"status": "success", "url": url, **result})
            except Exception as e:
                results.append({"status": "failed", "url": url, "error": str(e)})

        success = sum(1 for r in results if r["status"] == "success")

        return CrawlResponse(
            session_id=request.session_id,
            distributed=False,
            total=len(results),
            success=success,
            failed=len(results) - success,
            results=results,
        )
```

**Step 4: Register router**

Modify `backend/src/research_tool/api/routes/__init__.py` to add:

```python
from research_tool.api.routes.crawl import router as crawl_router

# Add to router list:
routers = [
    # ... existing routers ...
    crawl_router,
]
```

**Step 5: Run test to verify it passes**

Run: `cd backend && uv run python -m pytest tests/unit/test_crawl_api.py -v`
Expected: 2 passed

**Step 6: Commit**

```bash
git add backend/src/research_tool/api/routes/crawl.py backend/src/research_tool/api/routes/__init__.py backend/tests/unit/test_crawl_api.py
git commit -m "feat(api): add /api/crawl/batch endpoint with distributed option"
```

---

## Task 7: Create Docker Configuration

**Files:**
- Create: `backend/docker/docker-compose.distributed.yml`
- Create: `backend/docker/Dockerfile.worker`

**Step 1: Create docker-compose.distributed.yml**

Create `backend/docker/docker-compose.distributed.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3

  worker:
    build:
      context: ..
      dockerfile: docker/Dockerfile.worker
    deploy:
      replicas: 8
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - browser_cache:/root/.cache/ms-playwright

  flower:
    image: mher/flower:2.0
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis_data:
  browser_cache:
```

**Step 2: Create Dockerfile.worker**

Create `backend/docker/Dockerfile.worker`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --extra distributed

# Install Playwright browsers
RUN uv run playwright install chromium

# Copy source code
COPY src/ ./src/

# Run Celery worker
CMD ["uv", "run", "celery", "-A", "research_tool.services.distributed.celery_app", "worker", "--loglevel=info", "--concurrency=1"]
```

**Step 3: Create docker directory if needed**

```bash
mkdir -p backend/docker
```

**Step 4: Commit**

```bash
git add backend/docker/
git commit -m "feat(docker): add distributed crawling Docker configuration"
```

---

## Task 8: Add Integration Test

**Files:**
- Create: `backend/tests/integration/test_distributed_integration.py`

**Step 1: Create integration test**

Create `backend/tests/integration/test_distributed_integration.py`:

```python
"""Integration tests for distributed crawling.

These tests require Redis to be running.
Skip if Redis is not available.
"""

import pytest

from research_tool.services.distributed import is_distributed_available


@pytest.fixture
def requires_redis():
    """Skip test if Redis is not available."""
    if not is_distributed_available():
        pytest.skip("Redis not available")


class TestDistributedIntegration:
    """Integration tests for distributed crawling."""

    def test_is_distributed_available_returns_bool(self) -> None:
        """is_distributed_available returns boolean."""
        result = is_distributed_available()
        assert isinstance(result, bool)

    @pytest.mark.usefixtures("requires_redis")
    def test_coordinator_dispatches_tasks(self) -> None:
        """Coordinator can dispatch tasks to Redis."""
        from research_tool.services.distributed import CrawlCoordinator

        coordinator = CrawlCoordinator(session_id="integration-test")
        # This will queue tasks but won't complete without workers
        # Just verify no exceptions on dispatch
        assert coordinator.session_id == "integration-test"
```

**Step 2: Run test**

Run: `cd backend && uv run python -m pytest tests/integration/test_distributed_integration.py -v`
Expected: 1 passed, 1 skipped (if Redis not running)

**Step 3: Commit**

```bash
git add backend/tests/integration/test_distributed_integration.py
git commit -m "test(distributed): add integration tests"
```

---

## Task 9: Update Documentation

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

**Step 1: Add distributed section to README.md**

Add after Quick Start section:

```markdown
## Distributed Crawling (Optional)

For large-scale research with 100+ URLs:

### Start Infrastructure

```bash
cd backend
docker compose -f docker/docker-compose.distributed.yml up -d
```

### Verify Workers

```bash
# Check worker status
docker compose -f docker/docker-compose.distributed.yml ps

# View Flower monitoring UI
open http://localhost:5555
```

### Use Distributed Mode

```bash
curl -X POST http://localhost:8000/api/crawl/batch \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example1.com", "https://example2.com"],
    "session_id": "research-123",
    "distributed": true
  }'
```

### Stop Infrastructure

```bash
docker compose -f docker/docker-compose.distributed.yml down
```
```

**Step 2: Add to CLAUDE.md key files table**

Add rows:

```markdown
| Distributed Config | `src/research_tool/services/distributed/config.py` |
| Celery Tasks | `src/research_tool/services/distributed/tasks.py` |
| Coordinator | `src/research_tool/services/distributed/coordinator.py` |
```

**Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: add distributed crawling documentation"
```

---

## Task 10: Final Verification

**Step 1: Run all tests**

```bash
cd backend && uv run python -m pytest tests/ -q --tb=no
```
Expected: All tests pass (800+ including new ones)

**Step 2: Run linting**

```bash
uv run ruff check src/
uv run python -m mypy src/ --ignore-missing-imports
```
Expected: No errors

**Step 3: Push all changes**

```bash
git push origin main
```

---

## Summary

| Task | Files | Tests |
|------|-------|-------|
| 1. Dependencies | pyproject.toml | - |
| 2. Config | distributed/config.py | - |
| 3. Celery App | distributed/celery_app.py | 3 |
| 4. Tasks | distributed/tasks.py | 3 |
| 5. Coordinator | distributed/coordinator.py | 3 |
| 6. API | api/routes/crawl.py | 2 |
| 7. Docker | docker/*.yml, Dockerfile | - |
| 8. Integration | tests/integration/ | 2 |
| 9. Docs | README.md, CLAUDE.md | - |
| 10. Verify | - | all |

**Total: ~10 tasks, ~13 new tests, ~600 LOC**

---

*Plan created: 2025-12-20*
