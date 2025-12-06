"""Memory repository interface for research tool."""

from abc import ABC, abstractmethod


class MemoryRepository(ABC):
    """Abstract interface for memory operations."""

    @abstractmethod
    async def store_document(
        self,
        content: str,
        metadata: dict,
        session_id: str
    ) -> str:
        """Store document with embedding.

        Args:
            content: The document content to store
            metadata: Additional metadata about the document
            session_id: The research session ID

        Returns:
            str: The document ID
        """
        pass

    @abstractmethod
    async def search_similar(
        self,
        query: str,
        limit: int = 10,
        filters: dict | None = None
    ) -> list[dict]:
        """Search for similar documents using hybrid search.

        Args:
            query: The search query
            limit: Maximum number of results to return
            filters: Optional filters to apply

        Returns:
            list[dict]: List of matching documents with metadata
        """
        pass

    @abstractmethod
    async def get_source_effectiveness(
        self,
        source_name: str,
        domain: str | None = None
    ) -> float:
        """Get effectiveness score for a source.

        Args:
            source_name: Name of the source
            domain: Optional domain to filter by

        Returns:
            float: Effectiveness score between 0.0 and 1.0
        """
        pass

    @abstractmethod
    async def update_source_effectiveness(
        self,
        source_name: str,
        domain: str,
        success: bool,
        quality_score: float
    ) -> None:
        """Update source effectiveness using exponential moving average.

        Args:
            source_name: Name of the source
            domain: Domain the source was used for
            success: Whether the source successfully provided results
            quality_score: Quality score of the results (0.0 to 1.0)
        """
        pass

    @abstractmethod
    async def record_access_failure(
        self,
        url: str,
        source_name: str,
        error_type: str,
        error_message: str
    ) -> None:
        """Record permanent access failure.

        Args:
            url: The URL that failed
            source_name: Name of the source
            error_type: Type of error encountered
            error_message: Detailed error message
        """
        pass

    @abstractmethod
    async def is_known_failure(self, url: str) -> bool:
        """Check if URL is known to be inaccessible.

        Args:
            url: The URL to check

        Returns:
            bool: True if URL is known to fail
        """
        pass
