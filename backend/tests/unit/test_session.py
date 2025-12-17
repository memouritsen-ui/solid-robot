"""Tests for session persistence system."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from research_tool.services.session.storage import (
    SessionStorage,
    SessionData,
    get_session_storage,
    init_session_storage,
)


class TestSessionData:
    """Test SessionData dataclass."""

    def test_session_data_creation(self) -> None:
        """SessionData can be created with required fields."""
        data = SessionData(
            domain="example.com",
            cookies=[{"name": "session", "value": "abc123"}],
            local_storage={"key": "value"},
            session_storage={"temp": "data"},
        )
        assert data.domain == "example.com"
        assert len(data.cookies) == 1
        assert data.local_storage["key"] == "value"

    def test_session_data_defaults(self) -> None:
        """SessionData has sensible defaults."""
        data = SessionData(domain="example.com")
        assert data.cookies == []
        assert data.local_storage == {}
        assert data.session_storage == {}
        assert data.created_at is not None
        assert data.updated_at is not None


class TestSessionStorage:
    """Test SessionStorage class."""

    @pytest.mark.asyncio
    async def test_save_and_load_session(self) -> None:
        """Sessions can be saved and loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "sessions.db"
            storage = SessionStorage(str(db_path))

            # Save session
            data = SessionData(
                domain="example.com",
                cookies=[{"name": "auth", "value": "token123"}],
                local_storage={"user_id": "42"},
            )
            await storage.save_session(data)

            # Load session
            loaded = await storage.load_session("example.com")
            assert loaded is not None
            assert loaded.domain == "example.com"
            assert loaded.cookies[0]["value"] == "token123"
            assert loaded.local_storage["user_id"] == "42"

    @pytest.mark.asyncio
    async def test_load_nonexistent_session(self) -> None:
        """Loading nonexistent session returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "sessions.db"
            storage = SessionStorage(str(db_path))

            loaded = await storage.load_session("nonexistent.com")
            assert loaded is None

    @pytest.mark.asyncio
    async def test_update_session(self) -> None:
        """Saving to same domain updates existing session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "sessions.db"
            storage = SessionStorage(str(db_path))

            # Initial save
            data1 = SessionData(
                domain="example.com",
                cookies=[{"name": "v1", "value": "first"}],
            )
            await storage.save_session(data1)

            # Update
            data2 = SessionData(
                domain="example.com",
                cookies=[{"name": "v2", "value": "second"}],
            )
            await storage.save_session(data2)

            # Should have updated value
            loaded = await storage.load_session("example.com")
            assert loaded is not None
            assert loaded.cookies[0]["name"] == "v2"

    @pytest.mark.asyncio
    async def test_delete_session(self) -> None:
        """Sessions can be deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "sessions.db"
            storage = SessionStorage(str(db_path))

            # Save session
            data = SessionData(domain="example.com")
            await storage.save_session(data)

            # Verify exists
            assert await storage.load_session("example.com") is not None

            # Delete
            await storage.delete_session("example.com")

            # Verify deleted
            assert await storage.load_session("example.com") is None

    @pytest.mark.asyncio
    async def test_list_sessions(self) -> None:
        """All session domains can be listed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "sessions.db"
            storage = SessionStorage(str(db_path))

            # Save multiple sessions
            await storage.save_session(SessionData(domain="a.com"))
            await storage.save_session(SessionData(domain="b.com"))
            await storage.save_session(SessionData(domain="c.com"))

            domains = await storage.list_sessions()
            assert len(domains) == 3
            assert "a.com" in domains
            assert "b.com" in domains
            assert "c.com" in domains

    @pytest.mark.asyncio
    async def test_clear_all_sessions(self) -> None:
        """All sessions can be cleared."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "sessions.db"
            storage = SessionStorage(str(db_path))

            # Save multiple sessions
            await storage.save_session(SessionData(domain="a.com"))
            await storage.save_session(SessionData(domain="b.com"))

            # Clear all
            await storage.clear_all()

            # Verify empty
            domains = await storage.list_sessions()
            assert len(domains) == 0


class TestSessionExpiry:
    """Test session expiry functionality."""

    @pytest.mark.asyncio
    async def test_expired_session_not_returned(self) -> None:
        """Expired sessions are not returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "sessions.db"
            storage = SessionStorage(str(db_path), max_age=0)  # 0 seconds = immediate expiry

            # Save session
            data = SessionData(domain="example.com")
            await storage.save_session(data)

            # Should not return expired session
            loaded = await storage.load_session("example.com")
            assert loaded is None

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self) -> None:
        """Expired sessions can be cleaned up."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "sessions.db"
            storage = SessionStorage(str(db_path), max_age=0)

            # Save sessions
            await storage.save_session(SessionData(domain="a.com"))
            await storage.save_session(SessionData(domain="b.com"))

            # Cleanup
            removed = await storage.cleanup_expired()
            assert removed == 2

            # Verify empty
            domains = await storage.list_sessions()
            assert len(domains) == 0


class TestPlaywrightIntegration:
    """Test Playwright storage state integration."""

    @pytest.mark.asyncio
    async def test_from_playwright_storage_state(self) -> None:
        """Can create SessionData from Playwright storage state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "sessions.db"
            storage = SessionStorage(str(db_path))

            # Simulated Playwright storage state
            playwright_state = {
                "cookies": [
                    {"name": "session", "value": "abc", "domain": ".example.com"},
                    {"name": "prefs", "value": "dark", "domain": ".example.com"},
                ],
                "origins": [
                    {
                        "origin": "https://example.com",
                        "localStorage": [
                            {"name": "user", "value": "john"},
                        ],
                    }
                ],
            }

            data = storage.from_playwright_state("example.com", playwright_state)
            assert data.domain == "example.com"
            assert len(data.cookies) == 2
            assert data.local_storage["user"] == "john"

    @pytest.mark.asyncio
    async def test_to_playwright_storage_state(self) -> None:
        """Can convert SessionData to Playwright storage state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "sessions.db"
            storage = SessionStorage(str(db_path))

            data = SessionData(
                domain="example.com",
                cookies=[{"name": "session", "value": "xyz", "domain": ".example.com"}],
                local_storage={"theme": "light"},
            )

            state = storage.to_playwright_state(data)
            assert "cookies" in state
            assert len(state["cookies"]) == 1
            assert "origins" in state
            assert state["origins"][0]["localStorage"][0]["value"] == "light"


class TestGlobalAccessor:
    """Test global session storage accessor."""

    def test_get_session_storage_before_init(self) -> None:
        """get_session_storage returns None before initialization."""
        # Reset global state
        import research_tool.services.session.storage as storage_module
        storage_module._session_storage = None

        assert get_session_storage() is None

    def test_init_and_get_session_storage(self) -> None:
        """Session storage can be initialized and retrieved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "sessions.db"

            storage = init_session_storage(str(db_path))
            assert storage is not None

            retrieved = get_session_storage()
            assert retrieved is storage

            # Cleanup
            import research_tool.services.session.storage as storage_module
            storage_module._session_storage = None
