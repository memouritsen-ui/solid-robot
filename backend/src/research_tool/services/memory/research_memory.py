"""Research Memory Service - Persistent storage with FTS5 search.

Provides SQLite-based storage for research sessions with full-text search
capabilities across queries, facts, summaries, and source titles.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ResearchSession:
    """A complete research session with all collected data.

    Attributes:
        session_id: Unique identifier for the session
        query: Original research query
        domain: Research domain (academic, news, etc.)
        privacy_mode: Privacy mode used (local_only, cloud_allowed)
        status: Session status (running, completed, failed)
        summary: Generated summary of findings
        facts: List of extracted facts with confidence scores
        sources: List of sources used
        entities: List of discovered entities
        confidence_score: Overall confidence score
        started_at: When research started
        completed_at: When research completed
        saturation_metrics: Saturation data from evaluate phase
    """

    session_id: str
    query: str
    domain: str = "general"
    privacy_mode: str = "cloud_allowed"
    status: str = "completed"
    summary: str | None = None
    facts: list[dict[str, Any]] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    confidence_score: float | None = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    saturation_metrics: dict[str, Any] | None = None


@dataclass
class SearchResult:
    """A search result from FTS query.

    Attributes:
        session_id: Matched session ID
        query: Original query text
        summary: Session summary (may be truncated)
        started_at: When session started
        rank: FTS relevance rank
    """

    session_id: str
    query: str
    summary: str | None
    started_at: datetime
    rank: float = 0.0


@dataclass
class SessionSummary:
    """Brief summary of a session for listing.

    Attributes:
        session_id: Session identifier
        query: Original query text
        domain: Research domain
        status: Session status
        facts_count: Number of facts extracted
        sources_count: Number of sources used
        confidence_score: Overall confidence
        started_at: When session started
        completed_at: When session completed
    """

    session_id: str
    query: str
    domain: str
    status: str
    facts_count: int = 0
    sources_count: int = 0
    confidence_score: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class LibraryStats:
    """Statistics about the research library.

    Attributes:
        total_sessions: Total number of sessions
        total_facts: Total facts across all sessions
        total_sources: Total unique sources
        completed_sessions: Number of completed sessions
        average_confidence: Average confidence score
    """

    total_sessions: int = 0
    total_facts: int = 0
    total_sources: int = 0
    completed_sessions: int = 0
    average_confidence: float | None = None


class ResearchMemory:
    """SQLite-based research session storage with FTS5 search.

    Features:
    - Full-text search across queries, summaries, facts, and sources
    - CRUD operations for research sessions
    - Pagination support for listing
    - Aggregated statistics

    Example:
        memory = ResearchMemory("./data/research_memory.db")
        await memory.save_session(session)
        results = await memory.search_sessions("quantum computing")
    """

    def __init__(self, db_path: str = "./data/research_memory.db") -> None:
        """Initialize research memory storage.

        Args:
            db_path: Path to SQLite database file
        """
        self._db_path = Path(db_path)
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Create database schema if it doesn't exist."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self._db_path) as conn:
            # Main sessions table with full data
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_sessions_full (
                    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    query TEXT NOT NULL,
                    domain TEXT,
                    privacy_mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT,
                    facts TEXT,
                    sources TEXT,
                    entities TEXT,
                    confidence_score REAL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    saturation_metrics TEXT
                )
            """)

            # FTS5 virtual table for full-text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
                    session_id,
                    query,
                    summary,
                    facts_text,
                    source_titles,
                    content='research_sessions_full',
                    content_rowid='rowid'
                )
            """)

            # SQL helpers for FTS content extraction
            facts_sql = (
                "COALESCE((SELECT GROUP_CONCAT(json_extract(value, '$.claim'), ' ') "
                "FROM json_each({prefix}.facts)), '')"
            )
            sources_sql = (
                "COALESCE((SELECT GROUP_CONCAT(json_extract(value, '$.title'), ' ') "
                "FROM json_each({prefix}.sources)), '')"
            )

            # Triggers to keep FTS in sync
            conn.execute(f"""
                CREATE TRIGGER IF NOT EXISTS sessions_fts_insert
                AFTER INSERT ON research_sessions_full BEGIN
                    INSERT INTO sessions_fts(
                        rowid, session_id, query, summary, facts_text, source_titles
                    ) VALUES (
                        NEW.rowid, NEW.session_id, NEW.query,
                        COALESCE(NEW.summary, ''),
                        {facts_sql.format(prefix='NEW')},
                        {sources_sql.format(prefix='NEW')}
                    );
                END
            """)

            conn.execute(f"""
                CREATE TRIGGER IF NOT EXISTS sessions_fts_delete
                AFTER DELETE ON research_sessions_full BEGIN
                    INSERT INTO sessions_fts(
                        sessions_fts, rowid, session_id, query,
                        summary, facts_text, source_titles
                    ) VALUES (
                        'delete', OLD.rowid, OLD.session_id, OLD.query,
                        COALESCE(OLD.summary, ''),
                        {facts_sql.format(prefix='OLD')},
                        {sources_sql.format(prefix='OLD')}
                    );
                END
            """)

            conn.execute(f"""
                CREATE TRIGGER IF NOT EXISTS sessions_fts_update
                AFTER UPDATE ON research_sessions_full BEGIN
                    INSERT INTO sessions_fts(
                        sessions_fts, rowid, session_id, query,
                        summary, facts_text, source_titles
                    ) VALUES (
                        'delete', OLD.rowid, OLD.session_id, OLD.query,
                        COALESCE(OLD.summary, ''),
                        {facts_sql.format(prefix='OLD')},
                        {sources_sql.format(prefix='OLD')}
                    );
                    INSERT INTO sessions_fts(
                        rowid, session_id, query, summary, facts_text, source_titles
                    ) VALUES (
                        NEW.rowid, NEW.session_id, NEW.query,
                        COALESCE(NEW.summary, ''),
                        {facts_sql.format(prefix='NEW')},
                        {sources_sql.format(prefix='NEW')}
                    );
                END
            """)

            # Index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_full_started
                ON research_sessions_full(started_at DESC)
            """)

            conn.commit()

    async def save_session(self, session: ResearchSession) -> None:
        """Save or update a research session.

        Args:
            session: Research session to save
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT INTO research_sessions_full (
                    session_id, query, domain, privacy_mode, status,
                    summary, facts, sources, entities, confidence_score,
                    started_at, completed_at, saturation_metrics
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    query = excluded.query,
                    domain = excluded.domain,
                    privacy_mode = excluded.privacy_mode,
                    status = excluded.status,
                    summary = excluded.summary,
                    facts = excluded.facts,
                    sources = excluded.sources,
                    entities = excluded.entities,
                    confidence_score = excluded.confidence_score,
                    started_at = excluded.started_at,
                    completed_at = excluded.completed_at,
                    saturation_metrics = excluded.saturation_metrics
            """, (
                session.session_id,
                session.query,
                session.domain,
                session.privacy_mode,
                session.status,
                session.summary,
                json.dumps(session.facts) if session.facts else None,
                json.dumps(session.sources) if session.sources else None,
                json.dumps(session.entities) if session.entities else None,
                session.confidence_score,
                session.started_at.isoformat(),
                session.completed_at.isoformat() if session.completed_at else None,
                json.dumps(session.saturation_metrics) if session.saturation_metrics else None,
            ))
            conn.commit()

        logger.debug(f"session_saved: {session.session_id}")

    async def get_session(self, session_id: str) -> ResearchSession | None:
        """Get a research session by ID.

        Args:
            session_id: Session identifier

        Returns:
            ResearchSession if found, None otherwise
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM research_sessions_full WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_session(row)

    async def search_sessions(
        self,
        query: str,
        limit: int = 20
    ) -> list[SearchResult]:
        """Search sessions using FTS5.

        Args:
            query: Search query text
            limit: Maximum results to return

        Returns:
            List of SearchResult objects ranked by relevance
        """
        # Escape special FTS characters and create search query
        search_query = query.replace('"', '""')

        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT
                    r.session_id,
                    r.query,
                    r.summary,
                    r.started_at,
                    bm25(sessions_fts) as rank
                FROM sessions_fts f
                JOIN research_sessions_full r ON f.rowid = r.rowid
                WHERE sessions_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (search_query, limit))
            rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append(SearchResult(
                session_id=row["session_id"],
                query=row["query"],
                summary=row["summary"],
                started_at=datetime.fromisoformat(row["started_at"]),
                rank=row["rank"],
            ))

        return results

    async def list_sessions(
        self,
        offset: int = 0,
        limit: int = 20
    ) -> list[SessionSummary]:
        """List sessions with pagination.

        Args:
            offset: Number of sessions to skip
            limit: Maximum sessions to return

        Returns:
            List of SessionSummary objects, newest first
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT
                    session_id,
                    query,
                    domain,
                    status,
                    facts,
                    sources,
                    confidence_score,
                    started_at,
                    completed_at
                FROM research_sessions_full
                ORDER BY started_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = cursor.fetchall()

        summaries = []
        for row in rows:
            facts = json.loads(row["facts"]) if row["facts"] else []
            sources = json.loads(row["sources"]) if row["sources"] else []

            started = row["started_at"]
            completed = row["completed_at"]
            summaries.append(SessionSummary(
                session_id=row["session_id"],
                query=row["query"],
                domain=row["domain"] or "general",
                status=row["status"],
                facts_count=len(facts),
                sources_count=len(sources),
                confidence_score=row["confidence_score"],
                started_at=datetime.fromisoformat(started) if started else None,
                completed_at=datetime.fromisoformat(completed) if completed else None,
            ))

        return summaries

    async def delete_session(self, session_id: str) -> bool:
        """Delete a research session.

        Args:
            session_id: Session to delete

        Returns:
            True if session was deleted, False if not found
        """
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM research_sessions_full WHERE session_id = ?
            """, (session_id,))
            conn.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            logger.debug(f"session_deleted: {session_id}")

        return deleted

    async def get_statistics(self) -> LibraryStats:
        """Get library statistics.

        Returns:
            LibraryStats with aggregated data
        """
        with sqlite3.connect(self._db_path) as conn:
            # Total sessions
            cursor = conn.execute("SELECT COUNT(*) FROM research_sessions_full")
            total_sessions = cursor.fetchone()[0]

            # Completed sessions
            cursor = conn.execute(
                "SELECT COUNT(*) FROM research_sessions_full WHERE status = 'completed'"
            )
            completed_sessions = cursor.fetchone()[0]

            # Average confidence
            cursor = conn.execute("""
                SELECT AVG(confidence_score)
                FROM research_sessions_full
                WHERE confidence_score IS NOT NULL
            """)
            avg_confidence = cursor.fetchone()[0]

            # Count facts and sources
            cursor = conn.execute("SELECT facts, sources FROM research_sessions_full")
            rows = cursor.fetchall()

            total_facts = 0
            total_sources = 0
            for row in rows:
                if row[0]:
                    facts = json.loads(row[0])
                    total_facts += len(facts)
                if row[1]:
                    sources = json.loads(row[1])
                    total_sources += len(sources)

        return LibraryStats(
            total_sessions=total_sessions,
            total_facts=total_facts,
            total_sources=total_sources,
            completed_sessions=completed_sessions,
            average_confidence=avg_confidence,
        )

    def _row_to_session(self, row: sqlite3.Row) -> ResearchSession:
        """Convert database row to ResearchSession object."""
        completed = row["completed_at"]
        saturation = row["saturation_metrics"]
        return ResearchSession(
            session_id=row["session_id"],
            query=row["query"],
            domain=row["domain"] or "general",
            privacy_mode=row["privacy_mode"],
            status=row["status"],
            summary=row["summary"],
            facts=json.loads(row["facts"]) if row["facts"] else [],
            sources=json.loads(row["sources"]) if row["sources"] else [],
            entities=json.loads(row["entities"]) if row["entities"] else [],
            confidence_score=row["confidence_score"],
            started_at=datetime.fromisoformat(row["started_at"]),
            completed_at=datetime.fromisoformat(completed) if completed else None,
            saturation_metrics=json.loads(saturation) if saturation else None,
        )


# Global singleton
_research_memory: ResearchMemory | None = None


def get_research_memory() -> ResearchMemory | None:
    """Get global research memory instance."""
    return _research_memory


def init_research_memory(db_path: str = "./data/research_memory.db") -> ResearchMemory:
    """Initialize global research memory."""
    global _research_memory
    _research_memory = ResearchMemory(db_path)
    return _research_memory
