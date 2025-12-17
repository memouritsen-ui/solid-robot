"""Session persistence storage for browser sessions.

Provides SQLite-based storage for browser sessions including:
- Cookies
- localStorage
- sessionStorage

This enables authenticated scraping by persisting login sessions
across crawler restarts.
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
class SessionData:
    """Stored session data for a domain.

    Attributes:
        domain: The domain this session is for
        cookies: List of cookie dictionaries
        local_storage: localStorage key-value pairs
        session_storage: sessionStorage key-value pairs
        created_at: When the session was first created
        updated_at: When the session was last updated
    """

    domain: str
    cookies: list[dict[str, Any]] = field(default_factory=list)
    local_storage: dict[str, str] = field(default_factory=dict)
    session_storage: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class SessionStorage:
    """SQLite-based session storage.

    Features:
    - Persistent storage across restarts
    - Per-domain session isolation
    - Automatic expiry of old sessions
    - Playwright storage state compatibility
    """

    def __init__(
        self,
        db_path: str = "./data/sessions.db",
        max_age: int = 604800,  # 7 days in seconds
    ) -> None:
        """Initialize session storage.

        Args:
            db_path: Path to SQLite database file
            max_age: Maximum age of sessions in seconds (default: 7 days)
        """
        self._db_path = Path(db_path)
        self._max_age = max_age
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Create database and tables if they don't exist."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    domain TEXT PRIMARY KEY,
                    cookies TEXT NOT NULL,
                    local_storage TEXT NOT NULL,
                    session_storage TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    async def save_session(self, data: SessionData) -> None:
        """Save or update a session.

        Args:
            data: Session data to save
        """
        data.updated_at = datetime.now()

        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sessions
                (domain, cookies, local_storage, session_storage, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data.domain,
                json.dumps(data.cookies),
                json.dumps(data.local_storage),
                json.dumps(data.session_storage),
                data.created_at.isoformat(),
                data.updated_at.isoformat(),
            ))
            conn.commit()

        logger.debug(f"session_saved: {data.domain}")

    async def load_session(self, domain: str) -> SessionData | None:
        """Load a session for a domain.

        Args:
            domain: Domain to load session for

        Returns:
            SessionData if found and not expired, None otherwise
        """
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("""
                SELECT domain, cookies, local_storage, session_storage, created_at, updated_at
                FROM sessions
                WHERE domain = ?
            """, (domain,))
            row = cursor.fetchone()

        if not row:
            return None

        updated_at = datetime.fromisoformat(row[5])
        age_seconds = (datetime.now() - updated_at).total_seconds()

        if age_seconds > self._max_age:
            logger.debug(f"session_expired: {domain} (age: {age_seconds}s)")
            return None

        return SessionData(
            domain=row[0],
            cookies=json.loads(row[1]),
            local_storage=json.loads(row[2]),
            session_storage=json.loads(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            updated_at=updated_at,
        )

    async def delete_session(self, domain: str) -> None:
        """Delete a session.

        Args:
            domain: Domain to delete session for
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE domain = ?", (domain,))
            conn.commit()

        logger.debug(f"session_deleted: {domain}")

    async def list_sessions(self) -> list[str]:
        """List all stored session domains.

        Returns:
            List of domain names with stored sessions
        """
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("SELECT domain FROM sessions")
            return [row[0] for row in cursor.fetchall()]

    async def clear_all(self) -> None:
        """Delete all stored sessions."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM sessions")
            conn.commit()

        logger.info("sessions_cleared")

    async def cleanup_expired(self) -> int:
        """Remove expired sessions.

        Returns:
            Number of sessions removed
        """
        cutoff = datetime.now()
        removed = 0

        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("""
                SELECT domain, updated_at FROM sessions
            """)

            for row in cursor.fetchall():
                updated_at = datetime.fromisoformat(row[1])
                age_seconds = (cutoff - updated_at).total_seconds()

                if age_seconds > self._max_age:
                    conn.execute("DELETE FROM sessions WHERE domain = ?", (row[0],))
                    removed += 1

            conn.commit()

        if removed:
            logger.info(f"sessions_cleanup: removed {removed} expired sessions")

        return removed

    def from_playwright_state(
        self,
        domain: str,
        storage_state: dict[str, Any]
    ) -> SessionData:
        """Create SessionData from Playwright storage state.

        Args:
            domain: Domain this state belongs to
            storage_state: Playwright storage state dictionary

        Returns:
            SessionData populated from the storage state
        """
        cookies = storage_state.get("cookies", [])

        # Extract localStorage from origins
        local_storage: dict[str, str] = {}
        for origin in storage_state.get("origins", []):
            for item in origin.get("localStorage", []):
                local_storage[item["name"]] = item["value"]

        return SessionData(
            domain=domain,
            cookies=cookies,
            local_storage=local_storage,
            session_storage={},
        )

    def to_playwright_state(self, data: SessionData) -> dict[str, Any]:
        """Convert SessionData to Playwright storage state format.

        Args:
            data: Session data to convert

        Returns:
            Dictionary in Playwright storage state format
        """
        # Build localStorage items
        local_storage_items = [
            {"name": k, "value": v}
            for k, v in data.local_storage.items()
        ]

        return {
            "cookies": data.cookies,
            "origins": [
                {
                    "origin": f"https://{data.domain}",
                    "localStorage": local_storage_items,
                }
            ] if local_storage_items else [],
        }


# Global singleton
_session_storage: SessionStorage | None = None


def get_session_storage() -> SessionStorage | None:
    """Get global session storage instance.

    Returns:
        SessionStorage instance or None if not initialized
    """
    return _session_storage


def init_session_storage(db_path: str = "./data/sessions.db", **kwargs: Any) -> SessionStorage:
    """Initialize global session storage.

    Args:
        db_path: Path to SQLite database file
        **kwargs: Additional arguments for SessionStorage

    Returns:
        Initialized SessionStorage instance
    """
    global _session_storage
    _session_storage = SessionStorage(db_path, **kwargs)
    return _session_storage
