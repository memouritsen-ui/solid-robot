"""Semantic Scholar search provider with strict rate limiting."""

from datetime import datetime
from typing import Any

import httpx

from research_tool.core.logging import get_logger

from .provider import SearchProvider
from .rate_limiter import rate_limiter

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

    async def search(
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
            "limit": min(max_results, 100),  # API max is 100
            "fields": "title,abstract,url,authors,year,citationCount,venue,publicationTypes"
        }

        # Add optional filters
        if filters:
            if "year" in filters:
                params["year"] = str(filters["year"])
            if "fieldsOfStudy" in filters:
                params["fieldsOfStudy"] = str(filters["fieldsOfStudy"])

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/paper/search",
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as e:
                logger.error("semantic_scholar_error", error=str(e))
                return []

        results = []
        for p in data.get("data", []):
            paper_id = p.get("paperId")
            if not paper_id:
                continue

            # Build author list
            authors = [a.get("name", "Unknown") for a in p.get("authors", [])]

            results.append({
                "url": f"https://www.semanticscholar.org/paper/{paper_id}",
                "title": p.get("title", "Untitled"),
                "snippet": p.get("abstract", ""),
                "source_name": self.name,
                "full_content": None,  # API doesn't provide full text
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

        logger.info("semantic_scholar_search",
                   query=query,
                   results_count=len(results))

        return results

    async def is_available(self) -> bool:
        """Check if Semantic Scholar is available.

        Returns:
            bool: Always True - no API key required for basic access
        """
        return True
