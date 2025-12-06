"""Search provider abstract interface."""

from abc import ABC, abstractmethod


class SearchProvider(ABC):
    """Abstract interface for search providers."""

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
    async def search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict | None = None
    ) -> list[dict]:
        """Execute search and return standardized results.

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
