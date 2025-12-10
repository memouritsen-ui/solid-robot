"""Unpaywall open access finder."""

from datetime import datetime
from typing import Any

import httpx

from research_tool.core.config import Settings

from .provider import SearchProvider
from .rate_limiter import rate_limiter

settings = Settings()

# Unpaywall API base URL
UNPAYWALL_API_BASE = "https://api.unpaywall.org/v2"


class UnpaywallProvider(SearchProvider):
    """Unpaywall provider for finding open access versions of papers."""

    @property
    def name(self) -> str:
        """Provider identifier for Unpaywall."""
        return "unpaywall"

    @property
    def requests_per_second(self) -> float:
        """Rate limit: 10 RPS (100k/day allows bursts)."""
        return 10.0

    def __init__(self) -> None:
        """Initialize Unpaywall provider."""
        if not settings.unpaywall_email:
            raise ValueError("UNPAYWALL_EMAIL not configured")
        self.email = settings.unpaywall_email

    async def get_open_access(self, doi: str) -> dict[str, Any] | None:
        """Look up open access availability for a DOI.

        Args:
            doi: The DOI to look up (e.g., "10.1234/example")

        Returns:
            dict with OA info or None if DOI not found
        """
        await rate_limiter.acquire(self.name, self.requests_per_second)

        url = f"{UNPAYWALL_API_BASE}/{doi}"
        params = {"email": self.email}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)

            if response.status_code == 404:
                return None

            if response.status_code != 200:
                return None

            data = response.json()

            best_oa = data.get("best_oa_location")
            best_url = None
            if best_oa:
                best_url = best_oa.get("url_for_pdf") or best_oa.get("url")

            return {
                "doi": data.get("doi"),
                "title": data.get("title"),
                "is_oa": data.get("is_oa", False),
                "best_oa_url": best_url,
                "best_oa_location": best_oa,
                "oa_locations": data.get("oa_locations", []),
                "retrieved_at": datetime.now(),
            }

    async def search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search for open access versions of papers by DOI.

        Note: Unpaywall doesn't support text search. Use filters["dois"] to
        look up specific DOIs.

        Args:
            query: Ignored (Unpaywall requires DOIs)
            max_results: Maximum results to return
            filters: Must contain "dois" key with list of DOIs

        Returns:
            list[dict]: Standardized search results for OA papers
        """
        if not filters or "dois" not in filters:
            return []

        dois = filters["dois"][:max_results]
        results = []

        for doi in dois:
            oa_result = await self.get_open_access(doi)
            if oa_result and oa_result.get("is_oa") and oa_result.get("best_oa_url"):
                results.append({
                    "url": oa_result["best_oa_url"],
                    "title": oa_result.get("title", ""),
                    "snippet": f"Open access version of DOI: {doi}",
                    "source_name": self.name,
                    "full_content": None,
                    "retrieved_at": oa_result["retrieved_at"],
                    "metadata": {
                        "doi": doi,
                        "is_oa": True,
                        "oa_locations_count": len(oa_result.get("oa_locations", [])),
                    }
                })

        return results

    async def is_available(self) -> bool:
        """Check if Unpaywall is configured.

        Returns:
            bool: True if email is configured
        """
        return settings.unpaywall_email is not None
