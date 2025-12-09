"""SQLite repository implementation for structured data storage."""

import json
from pathlib import Path
from types import ModuleType
from typing import Any

try:
    import aiosqlite
except ImportError:
    # Fallback for when aiosqlite is not installed yet
    aiosqlite: ModuleType | None = None  # type: ignore[no-redef]


SCHEMA_SQL = """
-- Research sessions
CREATE TABLE IF NOT EXISTS research_sessions (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    domain TEXT,
    privacy_mode TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    saturation_metrics TEXT,  -- JSON
    final_report_path TEXT
);

-- Source effectiveness tracking
CREATE TABLE IF NOT EXISTS source_effectiveness (
    source_name TEXT NOT NULL,
    domain TEXT NOT NULL,
    effectiveness_score REAL NOT NULL DEFAULT 0.5,
    total_queries INTEGER NOT NULL DEFAULT 0,
    successful_queries INTEGER NOT NULL DEFAULT 0,
    avg_quality_score REAL,
    last_updated TIMESTAMP NOT NULL,
    PRIMARY KEY (source_name, domain)
);

-- Access failures (permanent record)
CREATE TABLE IF NOT EXISTS access_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT,
    first_failed_at TIMESTAMP NOT NULL,
    retry_count INTEGER DEFAULT 1
);

-- Domain configuration overrides (learned)
CREATE TABLE IF NOT EXISTS domain_config_overrides (
    domain TEXT PRIMARY KEY,
    preferred_sources TEXT,  -- JSON array
    excluded_sources TEXT,   -- JSON array
    custom_keywords TEXT,    -- JSON array
    updated_at TIMESTAMP NOT NULL
);

-- User preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_query ON research_sessions(query);
CREATE INDEX IF NOT EXISTS idx_sessions_domain ON research_sessions(domain);
CREATE INDEX IF NOT EXISTS idx_effectiveness_domain ON source_effectiveness(domain);
CREATE INDEX IF NOT EXISTS idx_failures_url ON access_failures(url);
"""


class SQLiteRepository:
    """SQLite implementation for structured data storage."""

    def __init__(self, db_path: str = "./data/research.db") -> None:
        """Initialize SQLite repository.

        Args:
            db_path: Path to SQLite database file
        """
        if aiosqlite is None:
            raise ImportError(
                "aiosqlite is required for SQLite operations. "
                "Install with: pip install aiosqlite"
            )

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """Create tables if not exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA_SQL)
            await db.commit()

    # Research Sessions
    async def create_session(
        self,
        session_id: str,
        query: str,
        domain: str | None,
        privacy_mode: str
    ) -> None:
        """Create a new research session.

        Args:
            session_id: Unique session identifier
            query: The research query
            domain: Optional domain classification
            privacy_mode: Privacy mode (LOCAL_ONLY, CLOUD_ALLOWED, etc.)
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO research_sessions
                (id, query, domain, privacy_mode, status, started_at)
                VALUES (?, ?, ?, ?, 'started', datetime('now'))
                """,
                (session_id, query, domain, privacy_mode)
            )
            await db.commit()

    async def update_session_status(
        self,
        session_id: str,
        status: str,
        saturation_metrics: dict[str, Any] | None = None,
        report_path: str | None = None
    ) -> None:
        """Update research session status.

        Args:
            session_id: Session identifier
            status: New status (started, in_progress, completed, failed)
            saturation_metrics: Optional saturation metrics dict
            report_path: Optional path to final report
        """
        async with aiosqlite.connect(self.db_path) as db:
            metrics_json = json.dumps(saturation_metrics) if saturation_metrics else None

            if status in ('completed', 'failed'):
                await db.execute(
                    """
                    UPDATE research_sessions
                    SET status = ?, completed_at = datetime('now'),
                        saturation_metrics = ?, final_report_path = ?
                    WHERE id = ?
                    """,
                    (status, metrics_json, report_path, session_id)
                )
            else:
                await db.execute(
                    """
                    UPDATE research_sessions
                    SET status = ?
                    WHERE id = ?
                    """,
                    (status, session_id)
                )
            await db.commit()

    # Source Effectiveness
    async def get_source_effectiveness(
        self,
        source_name: str,
        domain: str | None = None
    ) -> float | None:
        """Get effectiveness score for a source.

        Args:
            source_name: Name of the source
            domain: Optional domain to filter by

        Returns:
            float: Effectiveness score or None if not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            if domain:
                cursor = await db.execute(
                    """
                    SELECT effectiveness_score
                    FROM source_effectiveness
                    WHERE source_name = ? AND domain = ?
                    """,
                    (source_name, domain)
                )
            else:
                # Get average across all domains
                cursor = await db.execute(
                    """
                    SELECT AVG(effectiveness_score)
                    FROM source_effectiveness
                    WHERE source_name = ?
                    """,
                    (source_name,)
                )

            row = await cursor.fetchone()
            return float(row[0]) if row and row[0] is not None else None

    async def set_source_effectiveness(
        self,
        source_name: str,
        domain: str,
        effectiveness_score: float,
        quality_score: float | None = None,
        success: bool = True
    ) -> None:
        """Set source effectiveness score.

        Args:
            source_name: Name of the source
            domain: Domain the source was used for
            effectiveness_score: New effectiveness score (0.0 to 1.0)
            quality_score: Optional quality score for this query
            success: Whether the query was successful
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO source_effectiveness
                (source_name, domain, effectiveness_score, total_queries,
                 successful_queries, avg_quality_score, last_updated)
                VALUES (?, ?, ?, 1, ?, ?, datetime('now'))
                ON CONFLICT(source_name, domain) DO UPDATE SET
                    effectiveness_score = ?,
                    total_queries = total_queries + 1,
                    successful_queries = successful_queries + ?,
                    avg_quality_score = COALESCE(
                        (avg_quality_score * total_queries + ?) / (total_queries + 1),
                        ?
                    ),
                    last_updated = datetime('now')
                """,
                (
                    source_name, domain, effectiveness_score,
                    1 if success else 0,
                    quality_score,
                    effectiveness_score,
                    1 if success else 0,
                    quality_score if quality_score is not None else 0,
                    quality_score
                )
            )
            await db.commit()

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
        scores: list[tuple[str, float]] = []
        for source in available_sources:
            score = await self.get_source_effectiveness(source, domain)
            if score is None:
                score = 0.5  # Default for unknown sources
            scores.append((source, score))

        # Sort by score descending
        return sorted(scores, key=lambda x: x[1], reverse=True)

    # Access Failures
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
            error_type: Type of error (e.g., 'paywall', 'access_denied', 'timeout')
            error_message: Detailed error message
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO access_failures
                (url, source_name, error_type, error_message, first_failed_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                ON CONFLICT(url) DO UPDATE SET
                    retry_count = retry_count + 1
                """,
                (url, source_name, error_type, error_message)
            )
            await db.commit()

    async def is_known_failure(self, url: str) -> bool:
        """Check if URL is known to be inaccessible.

        Args:
            url: The URL to check

        Returns:
            bool: True if URL is known to fail
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT COUNT(*)
                FROM access_failures
                WHERE url = ?
                """,
                (url,)
            )
            row = await cursor.fetchone()
            return bool(row[0] > 0) if row else False

    async def get_failed_urls(self) -> list[str]:
        """Get list of all known failed URLs.

        Returns:
            list[str]: List of URLs known to fail
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT url FROM access_failures"
            )
            rows = await cursor.fetchall()
            return [str(row[0]) for row in rows]

    # Domain Config Overrides
    async def get_domain_config(self, domain: str) -> dict[str, Any] | None:
        """Get learned configuration overrides for a domain.

        Args:
            domain: Domain name

        Returns:
            dict: Configuration overrides or None if not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT preferred_sources, excluded_sources, custom_keywords
                FROM domain_config_overrides
                WHERE domain = ?
                """,
                (domain,)
            )
            row = await cursor.fetchone()
            if row:
                return {
                    "preferred_sources": json.loads(row[0]) if row[0] else [],
                    "excluded_sources": json.loads(row[1]) if row[1] else [],
                    "custom_keywords": json.loads(row[2]) if row[2] else []
                }
            return None

    async def update_domain_config(
        self,
        domain: str,
        preferred_sources: list[str] | None = None,
        excluded_sources: list[str] | None = None,
        custom_keywords: list[str] | None = None
    ) -> None:
        """Update learned configuration for a domain.

        Args:
            domain: Domain name
            preferred_sources: Optional list of preferred source names
            excluded_sources: Optional list of excluded source names
            custom_keywords: Optional list of custom keywords
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO domain_config_overrides
                (domain, preferred_sources, excluded_sources, custom_keywords, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                ON CONFLICT(domain) DO UPDATE SET
                    preferred_sources = COALESCE(?, preferred_sources),
                    excluded_sources = COALESCE(?, excluded_sources),
                    custom_keywords = COALESCE(?, custom_keywords),
                    updated_at = datetime('now')
                """,
                (
                    domain,
                    json.dumps(preferred_sources) if preferred_sources else None,
                    json.dumps(excluded_sources) if excluded_sources else None,
                    json.dumps(custom_keywords) if custom_keywords else None,
                    json.dumps(preferred_sources) if preferred_sources else None,
                    json.dumps(excluded_sources) if excluded_sources else None,
                    json.dumps(custom_keywords) if custom_keywords else None
                )
            )
            await db.commit()
