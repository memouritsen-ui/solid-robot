# SUPPLEMENT: Komplet Provider Kode

> **KRITISK:** Dette dokument indeholder den PRÆCISE kode for ALLE provider-opdateringer.
> Kopier koden PRÆCIST - ingen ændringer tilladt.

---

## Baggrund

Den originale plan sagde "gentag for hver provider" uden at give koden.
Dette dokument giver den EKSAKTE kode for hver provider.

---

## ÆNDRING TIL PROVIDER.PY BASE CLASS

**Fil:** `backend/src/research_tool/services/search/provider.py`

**ERSTAT HELE FILEN MED:**

```python
"""Search provider abstract interface with circuit breaker and retry integration."""

from abc import ABC, abstractmethod
from typing import Any

from research_tool.core.logging import get_logger
from research_tool.utils.circuit_breaker import get_circuit_breaker

logger = get_logger(__name__)


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

    async def search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute search with circuit breaker protection.

        This method wraps _do_search with circuit breaker.
        Subclasses should override _do_search, NOT this method.

        Args:
            query: The search query
            max_results: Maximum number of results to return
            filters: Optional filters (provider-specific)

        Returns:
            list[dict]: List of result dictionaries
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
            # Return empty instead of raising - graceful degradation
            return []

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
            list[dict]: List of result dictionaries with keys:
                - url: Result URL
                - title: Result title
                - snippet: Result snippet/abstract
                - source_name: Name of this provider
                - full_content: Optional full text content
                - metadata: Optional provider-specific metadata
        """
        pass

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

---

## BRAVE.PY - Komplet Opdatering

**Fil:** `backend/src/research_tool/services/search/brave.py`

**ERSTAT HELE FILEN MED:**

```python
"""Brave Search API provider with circuit breaker protection."""

from datetime import datetime
from typing import Any

import httpx

from research_tool.core.config import Settings
from research_tool.core.logging import get_logger
from research_tool.services.search.provider import SearchProvider
from research_tool.services.search.rate_limiter import rate_limiter
from research_tool.utils.retry import with_retry

settings = Settings()
logger = get_logger(__name__)


class BraveProvider(SearchProvider):
    """Brave Search API provider."""

    BASE_URL = "https://api.search.brave.com/res/v1"

    @property
    def name(self) -> str:
        """Provider identifier for Brave Search."""
        return "brave"

    @property
    def requests_per_second(self) -> float:
        """Rate limit: 1 RPS (conservative for Brave API)."""
        return 1.0

    @with_retry
    async def _do_search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search using Brave Search API.

        Args:
            query: Search query
            max_results: Maximum results to return
            filters: Optional filters (country, freshness, etc.)

        Returns:
            list[dict]: Standardized search results
        """
        if not settings.brave_api_key:
            logger.warning("brave_api_key_not_configured")
            return []

        await rate_limiter.acquire(self.name, self.requests_per_second)

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": settings.brave_api_key
        }

        params: dict[str, str | int] = {
            "q": query,
            "count": min(max_results, 20)
        }

        if filters:
            if "country" in filters:
                params["country"] = str(filters["country"])
            if "freshness" in filters:
                params["freshness"] = str(filters["freshness"])

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/web/search",
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for result in data.get("web", {}).get("results", []):
            results.append({
                "url": result.get("url", ""),
                "title": result.get("title", "Untitled"),
                "snippet": result.get("description", ""),
                "source_name": self.name,
                "full_content": None,
                "retrieved_at": datetime.now(),
                "metadata": {
                    "age": result.get("age"),
                    "language": result.get("language"),
                    "family_friendly": result.get("family_friendly", True)
                }
            })

        return results

    async def is_available(self) -> bool:
        """Check if Brave Search API is configured."""
        return settings.brave_api_key is not None
```

---

## SEMANTIC_SCHOLAR.PY - Komplet Opdatering

**Fil:** `backend/src/research_tool/services/search/semantic_scholar.py`

**ERSTAT HELE FILEN MED:**

```python
"""Semantic Scholar search provider with circuit breaker and strict rate limiting."""

from datetime import datetime
from typing import Any

import httpx

from research_tool.core.logging import get_logger
from research_tool.services.search.provider import SearchProvider
from research_tool.services.search.rate_limiter import rate_limiter
from research_tool.utils.retry import with_retry

logger = get_logger(__name__)


class SemanticScholarProvider(SearchProvider):
    """Semantic Scholar academic search provider.

    CRITICAL: Enforces strict 1 RPS rate limit as required by Semantic Scholar API.
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    @property
    def name(self) -> str:
        """Provider identifier for Semantic Scholar."""
        return "semantic_scholar"

    @property
    def requests_per_second(self) -> float:
        """Rate limit: 1 RPS (CRITICAL - do not exceed)."""
        return 1.0

    @with_retry
    async def _do_search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search Semantic Scholar with strict rate limiting.

        Args:
            query: Search query
            max_results: Maximum results (capped at 100)
            filters: Optional filters (year, fieldsOfStudy, etc.)

        Returns:
            list[dict]: Standardized search results
        """
        await rate_limiter.acquire(self.name, self.requests_per_second)

        params: dict[str, str | int] = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": "title,abstract,url,authors,year,citationCount,venue,publicationTypes"
        }

        if filters:
            if "year" in filters:
                params["year"] = str(filters["year"])
            if "fieldsOfStudy" in filters:
                params["fieldsOfStudy"] = str(filters["fieldsOfStudy"])

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/paper/search",
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for p in data.get("data", []):
            paper_id = p.get("paperId")
            if not paper_id:
                continue

            authors = [a.get("name", "Unknown") for a in p.get("authors", [])]

            results.append({
                "url": f"https://www.semanticscholar.org/paper/{paper_id}",
                "title": p.get("title", "Untitled"),
                "snippet": p.get("abstract", ""),
                "source_name": self.name,
                "full_content": None,
                "retrieved_at": datetime.now(),
                "metadata": {
                    "authors": authors,
                    "year": p.get("year"),
                    "citations": p.get("citationCount", 0),
                    "venue": p.get("venue"),
                    "publication_types": p.get("publicationTypes", []),
                    "paper_id": paper_id
                }
            })

        return results

    async def is_available(self) -> bool:
        """Check if Semantic Scholar is available."""
        return True
```

---

## PUBMED.PY - Komplet Opdatering

**Fil:** `backend/src/research_tool/services/search/pubmed.py`

**ÆNDRING:** Rename `search()` til `_do_search()` og tilføj `@with_retry`

Find og erstat:
```python
    async def search(
```

Med:
```python
    @with_retry
    async def _do_search(
```

Tilføj import øverst:
```python
from research_tool.utils.retry import with_retry
```

---

## ARXIV.PY - Komplet Opdatering

**Fil:** `backend/src/research_tool/services/search/arxiv.py`

**ÆNDRING:** Rename `search()` til `_do_search()` og tilføj `@with_retry`

Find og erstat:
```python
    async def search(
```

Med:
```python
    @with_retry
    async def _do_search(
```

Tilføj import øverst:
```python
from research_tool.utils.retry import with_retry
```

---

## EXA.PY - Komplet Opdatering

**Fil:** `backend/src/research_tool/services/search/exa.py`

**ÆNDRING:** Rename `search()` til `_do_search()` og tilføj `@with_retry`

Find og erstat:
```python
    async def search(
```

Med:
```python
    @with_retry
    async def _do_search(
```

Tilføj import øverst:
```python
from research_tool.utils.retry import with_retry
```

---

## TAVILY.PY - Komplet Opdatering

**Fil:** `backend/src/research_tool/services/search/tavily.py`

**ÆNDRING:** Rename `search()` til `_do_search()` og tilføj `@with_retry`

Find og erstat:
```python
    async def search(
```

Med:
```python
    @with_retry
    async def _do_search(
```

Tilføj import øverst:
```python
from research_tool.utils.retry import with_retry
```

---

## UNPAYWALL.PY - Komplet Opdatering

**Fil:** `backend/src/research_tool/services/search/unpaywall.py`

**ÆNDRING:** Rename `search()` til `_do_search()` og tilføj `@with_retry`

Find og erstat:
```python
    async def search(
```

Med:
```python
    @with_retry
    async def _do_search(
```

Tilføj import øverst:
```python
from research_tool.utils.retry import with_retry
```

---

## CRAWLER.PY - Allerede OK

Crawler bruger allerede `@with_retry` men har stadig `search()` metode.

**ÆNDRING:** Rename `search()` til `_do_search()`

Find og erstat:
```python
    @with_retry
    async def search(
```

Med:
```python
    @with_retry
    async def _do_search(
```

---

## VERIFICERING

Efter ALLE ændringer, kør:

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend
uv run python -m pytest tests/unit/test_provider.py tests/unit/test_tavily.py tests/unit/test_brave.py tests/unit/test_semantic_scholar.py tests/unit/test_pubmed.py tests/unit/test_arxiv.py -v
uv run ruff check src/research_tool/services/search/
uv run python -m mypy src/research_tool/services/search/ --ignore-missing-imports
```

**Expected:** Alle tests fejler fordi de kalder `search()` direkte.

**Handling:** Tests skal opdateres til at kalde `search()` (som nu wrapper `_do_search()`).

---

*Dette dokument indeholder PRÆCIS kode - INGEN improvisation tilladt.*
