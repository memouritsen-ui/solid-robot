"""arXiv search provider for preprints and academic papers."""

from datetime import datetime
from typing import Any

import arxiv

from research_tool.core.logging import get_logger

from .provider import SearchProvider
from .rate_limiter import rate_limiter

logger = get_logger(__name__)


class ArxivProvider(SearchProvider):
    """arXiv preprint search provider."""

    @property
    def name(self) -> str:
        return "arxiv"

    @property
    def requests_per_second(self) -> float:
        return 1.0  # Conservative rate limit for arXiv API

    def __init__(self) -> None:
        """Initialize arXiv client."""
        self.client = arxiv.Client()

    async def search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search arXiv for academic preprints.

        Args:
            query: Search query
            max_results: Maximum results to return
            filters: Optional filters (category, date range, etc.)

        Returns:
            list[dict]: Standardized search results
        """
        await rate_limiter.acquire(self.name, self.requests_per_second)

        try:
            # Build search
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )

            # Execute search (synchronous)
            results_list = []
            for result in self.client.results(search):
                # Extract authors
                authors = [author.name for author in result.authors]

                # Extract categories
                categories = result.categories

                results_list.append({
                    "url": result.entry_id,
                    "title": result.title,
                    "snippet": result.summary[:500] if result.summary else "",  # Limit snippet
                    "source_name": self.name,
                    "full_content": result.summary,  # Full abstract
                    "retrieved_at": datetime.now(),
                    "metadata": {
                        "authors": authors,
                        "published": result.published.isoformat() if result.published else None,
                        "updated": result.updated.isoformat() if result.updated else None,
                        "categories": categories,
                        "primary_category": result.primary_category,
                        "doi": result.doi,
                        "pdf_url": result.pdf_url,
                        "comment": result.comment
                    }
                })

            logger.info("arxiv_search", query=query, results_count=len(results_list))

            return results_list

        except Exception as e:
            logger.error("arxiv_search_error", error=str(e))
            return []

    async def is_available(self) -> bool:
        """Check if arXiv is available.

        Returns:
            bool: Always True - no API key required
        """
        return True
