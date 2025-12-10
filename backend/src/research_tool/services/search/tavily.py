"""Tavily AI search provider."""

from datetime import datetime
from typing import Any

from tavily import TavilyClient

from research_tool.core.config import Settings

from .provider import SearchProvider
from .rate_limiter import rate_limiter

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

    async def _do_search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Internal Tavily search implementation.

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
