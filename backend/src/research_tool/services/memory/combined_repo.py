"""Combined memory repository using LanceDB and SQLite."""


from .lance_repo import LanceDBRepository
from .learning import SourceLearning
from .repository import MemoryRepository
from .sqlite_repo import SQLiteRepository


class CombinedMemoryRepository(MemoryRepository):
    """Combines LanceDB and SQLite for full memory system.

    - LanceDB: Vector storage and hybrid search
    - SQLite: Structured data, source effectiveness, access failures
    - Learning: Source effectiveness tracking with EMA
    """

    def __init__(
        self,
        lance_db_path: str = "./data/lance_db",
        sqlite_db_path: str = "./data/research.db"
    ):
        """Initialize combined memory repository.

        Args:
            lance_db_path: Path to LanceDB database
            sqlite_db_path: Path to SQLite database
        """
        self.lance = LanceDBRepository(lance_db_path)
        self.sqlite = SQLiteRepository(sqlite_db_path)
        self.learning = SourceLearning(self.sqlite)
        self._initialized = False

    async def initialize(self):
        """Initialize both databases."""
        if not self._initialized:
            await self.sqlite.initialize()
            # LanceDB initializes on first use
            self._initialized = True

    async def store_document(
        self,
        content: str,
        metadata: dict,
        session_id: str
    ) -> str:
        """Store document in LanceDB with embedding.

        Args:
            content: The document content to store
            metadata: Additional metadata about the document
            session_id: The research session ID

        Returns:
            str: The document ID
        """
        await self.initialize()
        return await self.lance.store_document(content, metadata, session_id)

    async def search_similar(
        self,
        query: str,
        limit: int = 10,
        filters: dict | None = None
    ) -> list[dict]:
        """Search for similar documents using hybrid search in LanceDB.

        Args:
            query: The search query
            limit: Maximum number of results to return
            filters: Optional filters to apply

        Returns:
            list[dict]: List of matching documents with metadata
        """
        await self.initialize()
        return await self.lance.search_similar(query, limit, filters)

    async def get_source_effectiveness(
        self,
        source_name: str,
        domain: str | None = None
    ) -> float:
        """Get effectiveness score for a source from SQLite.

        Args:
            source_name: Name of the source
            domain: Optional domain to filter by

        Returns:
            float: Effectiveness score between 0.0 and 1.0
        """
        await self.initialize()
        score = await self.sqlite.get_source_effectiveness(source_name, domain)
        return score if score is not None else 0.5  # Default for unknown sources

    async def update_source_effectiveness(
        self,
        source_name: str,
        domain: str,
        success: bool,
        quality_score: float
    ) -> None:
        """Update source effectiveness using EMA via learning system.

        Args:
            source_name: Name of the source
            domain: Domain the source was used for
            success: Whether the source successfully provided results
            quality_score: Quality score of the results (0.0 to 1.0)
        """
        await self.initialize()
        await self.learning.update_effectiveness(
            source_name=source_name,
            domain=domain,
            success=success,
            quality_score=quality_score
        )

    async def record_access_failure(
        self,
        url: str,
        source_name: str,
        error_type: str,
        error_message: str
    ) -> None:
        """Record permanent access failure in SQLite.

        Args:
            url: The URL that failed
            source_name: Name of the source
            error_type: Type of error encountered
            error_message: Detailed error message
        """
        await self.initialize()
        await self.sqlite.record_access_failure(
            url=url,
            source_name=source_name,
            error_type=error_type,
            error_message=error_message
        )

    async def is_known_failure(self, url: str) -> bool:
        """Check if URL is known to be inaccessible in SQLite.

        Args:
            url: The URL to check

        Returns:
            bool: True if URL is known to fail
        """
        await self.initialize()
        return await self.sqlite.is_known_failure(url)

    async def get_ranked_sources(
        self,
        domain: str,
        available_sources: list[str]
    ) -> list[tuple[str, float]]:
        """Get sources ranked by effectiveness for domain.

        Args:
            domain: Domain to get rankings for
            available_sources: List of available source names

        Returns:
            list[tuple[str, float]]: List of (source_name, score) tuples, sorted descending
        """
        await self.initialize()
        return await self.learning.get_ranked_sources(domain, available_sources)

    async def get_failed_urls(self) -> list[str]:
        """Get list of all known failed URLs.

        Returns:
            list[str]: List of URLs known to fail
        """
        await self.initialize()
        return await self.sqlite.get_failed_urls()

    async def create_session(
        self,
        session_id: str,
        query: str,
        domain: str | None,
        privacy_mode: str
    ) -> None:
        """Create a new research session record.

        Args:
            session_id: Unique session identifier
            query: The research query
            domain: Optional domain classification
            privacy_mode: Privacy mode setting
        """
        await self.initialize()
        await self.sqlite.create_session(
            session_id=session_id,
            query=query,
            domain=domain,
            privacy_mode=privacy_mode
        )

    async def update_session_status(
        self,
        session_id: str,
        status: str,
        saturation_metrics: dict | None = None,
        report_path: str | None = None
    ) -> None:
        """Update research session status.

        Args:
            session_id: Session identifier
            status: New status
            saturation_metrics: Optional saturation metrics
            report_path: Optional path to final report
        """
        await self.initialize()
        await self.sqlite.update_session_status(
            session_id=session_id,
            status=status,
            saturation_metrics=saturation_metrics,
            report_path=report_path
        )
