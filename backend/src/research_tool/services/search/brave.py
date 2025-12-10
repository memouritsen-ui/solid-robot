"""Brave Search API provider."""

from datetime import datetime
from typing import Any

import httpx

from research_tool.core.config import Settings
from research_tool.core.logging import get_logger

from .provider import SearchProvider
from .rate_limiter import rate_limiter

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

    async def search(
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
            "count": min(max_results, 20)  # API max
        }

        # Add optional filters
        if filters:
            if "country" in filters:
                params["country"] = str(filters["country"])
            if "freshness" in filters:
                params["freshness"] = str(filters["freshness"])

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/web/search",
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as e:
                logger.error("brave_search_error", error=str(e))
                return []

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

        logger.info("brave_search", query=query, results_count=len(results))

        return results

    async def is_available(self) -> bool:
        """Check if Brave Search API is configured.

        Returns:
            bool: True if API key is configured
        """
        return settings.brave_api_key is not None
