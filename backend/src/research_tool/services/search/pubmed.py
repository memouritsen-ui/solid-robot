"""PubMed search provider for medical literature."""

from datetime import datetime

import httpx

from research_tool.core.logging import get_logger

from .provider import SearchProvider
from .rate_limiter import rate_limiter

logger = get_logger(__name__)


class PubMedProvider(SearchProvider):
    """PubMed medical literature search provider."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    @property
    def name(self) -> str:
        return "pubmed"

    @property
    def requests_per_second(self) -> float:
        return 3.0  # NCBI E-utilities rate limit (no API key)

    async def search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict | None = None
    ) -> list[dict]:
        """Search PubMed using E-utilities API.

        Args:
            query: Search query
            max_results: Maximum results to return
            filters: Optional filters (date range, publication type, etc.)

        Returns:
            list[dict]: Standardized search results
        """
        await rate_limiter.acquire(self.name, self.requests_per_second)

        # Step 1: Search for PMIDs
        async with httpx.AsyncClient() as client:
            try:
                search_response = await client.get(
                    f"{self.BASE_URL}/esearch.fcgi",
                    params={
                        "db": "pubmed",
                        "term": query,
                        "retmax": max_results,
                        "retmode": "json"
                    },
                    timeout=30.0
                )
                search_response.raise_for_status()
                search_data = search_response.json()
            except httpx.HTTPError as e:
                logger.error("pubmed_search_error", error=str(e))
                return []

        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return []

        # Step 2: Fetch article details
        await rate_limiter.acquire(self.name, self.requests_per_second)

        async with httpx.AsyncClient() as client:
            try:
                fetch_response = await client.get(
                    f"{self.BASE_URL}/esummary.fcgi",
                    params={
                        "db": "pubmed",
                        "id": ",".join(pmids),
                        "retmode": "json"
                    },
                    timeout=30.0
                )
                fetch_response.raise_for_status()
                fetch_data = fetch_response.json()
            except httpx.HTTPError as e:
                logger.error("pubmed_fetch_error", error=str(e))
                return []

        results = []
        for pmid in pmids:
            article = fetch_data.get("result", {}).get(pmid)
            if not article:
                continue

            # Extract authors
            authors = []
            for author in article.get("authors", []):
                name = author.get("name", "Unknown")
                authors.append(name)

            results.append({
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "title": article.get("title", "Untitled"),
                "snippet": article.get("source", ""),  # Journal info
                "source_name": self.name,
                "full_content": None,  # Would need additional API call
                "retrieved_at": datetime.now(),
                "metadata": {
                    "pmid": pmid,
                    "authors": authors,
                    "journal": article.get("fulljournalname"),
                    "pub_date": article.get("pubdate"),
                    "pub_type": article.get("pubtype", []),
                    "doi": article.get("elocationid", "")
                }
            })

        logger.info("pubmed_search", query=query, results_count=len(results))

        return results

    async def is_available(self) -> bool:
        """Check if PubMed is available.

        Returns:
            bool: Always True - no API key required
        """
        return True
