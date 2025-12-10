"""Exa AI search provider."""

from datetime import datetime
from typing import Any

from exa_py import Exa

from research_tool.core.config import Settings

from .provider import SearchProvider
from .rate_limiter import rate_limiter

settings = Settings()


class ExaProvider(SearchProvider):
    """Exa AI search provider with neural search capabilities."""

    @property
    def name(self) -> str:
        """Provider identifier for Exa AI."""
        return "exa"

    @property
    def requests_per_second(self) -> float:
        """Rate limit: 1 RPS (conservative for Exa API)."""
        return 1.0

    def __init__(self) -> None:
        """Initialize Exa client."""
        if not settings.exa_api_key:
            raise ValueError("EXA_API_KEY not configured")
        self.client = Exa(api_key=settings.exa_api_key)

    async def search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute Exa search with neural mode and text content.

        Args:
            query: Search query
            max_results: Maximum results to return
            filters: Optional filters (include_domains, exclude_domains, etc.)

        Returns:
            list[dict]: Standardized search results
        """
        await rate_limiter.acquire(self.name, self.requests_per_second)

        # Build search parameters
        search_params: dict[str, Any] = {
            "query": query,
            "num_results": max_results,
            "type": "neural",  # Best quality results
            "text": True,  # Include full text content
        }

        # Apply optional filters
        if filters:
            if "include_domains" in filters:
                search_params["include_domains"] = filters["include_domains"]
            if "exclude_domains" in filters:
                search_params["exclude_domains"] = filters["exclude_domains"]
            if "start_published_date" in filters:
                search_params["start_published_date"] = filters["start_published_date"]
            if "end_published_date" in filters:
                search_params["end_published_date"] = filters["end_published_date"]

        # Execute search with content retrieval
        response = self.client.search_and_contents(**search_params)

        results = []
        for r in response.results:
            results.append({
                "url": r.url,
                "title": r.title,
                "snippet": getattr(r, "text", "")[:500] if getattr(r, "text", None) else "",
                "source_name": self.name,
                "full_content": getattr(r, "text", None),
                "retrieved_at": datetime.now(),
                "metadata": {
                    "score": getattr(r, "score", None),
                    "published_date": getattr(r, "published_date", None),
                    "author": getattr(r, "author", None),
                }
            })

        return results

    async def is_available(self) -> bool:
        """Check if Exa is configured and accessible.

        Returns:
            bool: True if API key is configured
        """
        return settings.exa_api_key is not None
