"""Unit tests for ResearchMemory service.

Tests FTS5 search, CRUD operations, and session persistence.
"""

from __future__ import annotations

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from research_tool.services.memory.research_memory import (
    ResearchMemory,
    ResearchSession,
    SearchResult,
    SessionSummary,
    LibraryStats,
)


@pytest.fixture
def temp_db_path() -> str:
    """Create a temporary database path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        return f.name


@pytest.fixture
def research_memory(temp_db_path: str) -> ResearchMemory:
    """Create a ResearchMemory instance with temp database."""
    return ResearchMemory(db_path=temp_db_path)


@pytest.fixture
def sample_session() -> ResearchSession:
    """Create a sample research session for testing."""
    return ResearchSession(
        session_id="test-session-001",
        query="What is quantum computing?",
        domain="academic",
        privacy_mode="cloud_allowed",
        status="completed",
        summary="Quantum computing uses quantum mechanics principles for computation.",
        facts=[
            {"claim": "Quantum computers use qubits", "confidence": 0.95},
            {"claim": "Qubits can be in superposition", "confidence": 0.92},
        ],
        sources=[
            {"url": "https://example.com/quantum", "title": "Quantum Computing Guide"},
            {"url": "https://arxiv.org/123", "title": "Quantum Mechanics Paper"},
        ],
        entities=["quantum computing", "qubits", "superposition"],
        confidence_score=0.88,
        started_at=datetime(2025, 12, 17, 10, 0, 0),
        completed_at=datetime(2025, 12, 17, 10, 15, 0),
        saturation_metrics={"overall_saturation": 0.85},
    )


class TestResearchMemorySaveAndLoad:
    """Test saving and loading sessions."""

    @pytest.mark.asyncio
    async def test_save_session_creates_record(
        self, research_memory: ResearchMemory, sample_session: ResearchSession
    ) -> None:
        """Saving a session should create a database record."""
        await research_memory.save_session(sample_session)

        loaded = await research_memory.get_session(sample_session.session_id)
        assert loaded is not None
        assert loaded.session_id == sample_session.session_id
        assert loaded.query == sample_session.query

    @pytest.mark.asyncio
    async def test_get_session_returns_none_for_missing(
        self, research_memory: ResearchMemory
    ) -> None:
        """Getting a non-existent session should return None."""
        result = await research_memory.get_session("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_save_session_preserves_facts(
        self, research_memory: ResearchMemory, sample_session: ResearchSession
    ) -> None:
        """Saved session should preserve facts list."""
        await research_memory.save_session(sample_session)
        loaded = await research_memory.get_session(sample_session.session_id)

        assert loaded is not None
        assert len(loaded.facts) == 2
        assert loaded.facts[0]["claim"] == "Quantum computers use qubits"

    @pytest.mark.asyncio
    async def test_save_session_preserves_sources(
        self, research_memory: ResearchMemory, sample_session: ResearchSession
    ) -> None:
        """Saved session should preserve sources list."""
        await research_memory.save_session(sample_session)
        loaded = await research_memory.get_session(sample_session.session_id)

        assert loaded is not None
        assert len(loaded.sources) == 2
        assert loaded.sources[0]["title"] == "Quantum Computing Guide"

    @pytest.mark.asyncio
    async def test_save_session_update_existing(
        self, research_memory: ResearchMemory, sample_session: ResearchSession
    ) -> None:
        """Saving an existing session should update it."""
        await research_memory.save_session(sample_session)

        # Update and save again
        sample_session.summary = "Updated summary"
        await research_memory.save_session(sample_session)

        loaded = await research_memory.get_session(sample_session.session_id)
        assert loaded is not None
        assert loaded.summary == "Updated summary"


class TestResearchMemorySearch:
    """Test full-text search functionality."""

    @pytest.mark.asyncio
    async def test_search_by_query_text(
        self, research_memory: ResearchMemory, sample_session: ResearchSession
    ) -> None:
        """Should find sessions by query text."""
        await research_memory.save_session(sample_session)

        results = await research_memory.search_sessions("quantum computing")
        assert len(results) >= 1
        assert results[0].session_id == sample_session.session_id

    @pytest.mark.asyncio
    async def test_search_by_fact_content(
        self, research_memory: ResearchMemory, sample_session: ResearchSession
    ) -> None:
        """Should find sessions by fact content."""
        await research_memory.save_session(sample_session)

        results = await research_memory.search_sessions("qubits superposition")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_by_summary(
        self, research_memory: ResearchMemory, sample_session: ResearchSession
    ) -> None:
        """Should find sessions by summary text."""
        await research_memory.save_session(sample_session)

        results = await research_memory.search_sessions("quantum mechanics principles")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_returns_empty_for_no_match(
        self, research_memory: ResearchMemory, sample_session: ResearchSession
    ) -> None:
        """Should return empty list when no matches."""
        await research_memory.save_session(sample_session)

        results = await research_memory.search_sessions("blockchain cryptocurrency")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_respects_limit(
        self, research_memory: ResearchMemory
    ) -> None:
        """Search should respect the limit parameter."""
        # Create multiple sessions
        for i in range(5):
            session = ResearchSession(
                session_id=f"session-{i}",
                query=f"Quantum research topic {i}",
                domain="academic",
                privacy_mode="cloud_allowed",
                status="completed",
                summary=f"Summary about quantum topic {i}",
                facts=[],
                sources=[],
                entities=[],
                confidence_score=0.8,
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )
            await research_memory.save_session(session)

        results = await research_memory.search_sessions("quantum", limit=3)
        assert len(results) == 3


class TestResearchMemoryList:
    """Test listing sessions."""

    @pytest.mark.asyncio
    async def test_list_sessions_returns_summaries(
        self, research_memory: ResearchMemory, sample_session: ResearchSession
    ) -> None:
        """Listing sessions should return summaries."""
        await research_memory.save_session(sample_session)

        summaries = await research_memory.list_sessions()
        assert len(summaries) == 1
        assert summaries[0].session_id == sample_session.session_id
        assert summaries[0].query == sample_session.query

    @pytest.mark.asyncio
    async def test_list_sessions_pagination(
        self, research_memory: ResearchMemory
    ) -> None:
        """Listing should support pagination."""
        # Create 5 sessions
        for i in range(5):
            session = ResearchSession(
                session_id=f"session-{i}",
                query=f"Query {i}",
                domain="academic",
                privacy_mode="cloud_allowed",
                status="completed",
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )
            await research_memory.save_session(session)

        # Get first page
        page1 = await research_memory.list_sessions(offset=0, limit=2)
        assert len(page1) == 2

        # Get second page
        page2 = await research_memory.list_sessions(offset=2, limit=2)
        assert len(page2) == 2

        # Ensure no overlap
        ids1 = {s.session_id for s in page1}
        ids2 = {s.session_id for s in page2}
        assert ids1.isdisjoint(ids2)

    @pytest.mark.asyncio
    async def test_list_sessions_ordered_by_date(
        self, research_memory: ResearchMemory
    ) -> None:
        """Sessions should be ordered by date, newest first."""
        # Create sessions with different dates
        for i in range(3):
            session = ResearchSession(
                session_id=f"session-{i}",
                query=f"Query {i}",
                domain="academic",
                privacy_mode="cloud_allowed",
                status="completed",
                started_at=datetime(2025, 12, 10 + i, 10, 0, 0),
                completed_at=datetime(2025, 12, 10 + i, 10, 15, 0),
            )
            await research_memory.save_session(session)

        summaries = await research_memory.list_sessions()
        # Should be newest first (session-2 has Dec 12)
        assert summaries[0].session_id == "session-2"


class TestResearchMemoryDelete:
    """Test deleting sessions."""

    @pytest.mark.asyncio
    async def test_delete_session_removes_record(
        self, research_memory: ResearchMemory, sample_session: ResearchSession
    ) -> None:
        """Deleting a session should remove it."""
        await research_memory.save_session(sample_session)

        result = await research_memory.delete_session(sample_session.session_id)
        assert result is True

        loaded = await research_memory.get_session(sample_session.session_id)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(
        self, research_memory: ResearchMemory
    ) -> None:
        """Deleting non-existent session should return False."""
        result = await research_memory.delete_session("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_removes_from_fts(
        self, research_memory: ResearchMemory, sample_session: ResearchSession
    ) -> None:
        """Deleted session should not appear in search results."""
        await research_memory.save_session(sample_session)

        # Verify it's searchable
        results = await research_memory.search_sessions("quantum")
        assert len(results) >= 1

        # Delete it
        await research_memory.delete_session(sample_session.session_id)

        # Should no longer be searchable
        results = await research_memory.search_sessions("quantum")
        assert len(results) == 0


class TestResearchMemoryStatistics:
    """Test library statistics."""

    @pytest.mark.asyncio
    async def test_get_statistics_empty(
        self, research_memory: ResearchMemory
    ) -> None:
        """Statistics for empty library."""
        stats = await research_memory.get_statistics()
        assert stats.total_sessions == 0
        assert stats.total_facts == 0
        assert stats.total_sources == 0

    @pytest.mark.asyncio
    async def test_get_statistics_with_sessions(
        self, research_memory: ResearchMemory, sample_session: ResearchSession
    ) -> None:
        """Statistics should reflect stored sessions."""
        await research_memory.save_session(sample_session)

        stats = await research_memory.get_statistics()
        assert stats.total_sessions == 1
        assert stats.total_facts == 2  # sample_session has 2 facts
        assert stats.total_sources == 2  # sample_session has 2 sources

    @pytest.mark.asyncio
    async def test_statistics_aggregates_multiple_sessions(
        self, research_memory: ResearchMemory
    ) -> None:
        """Statistics should aggregate across sessions."""
        for i in range(3):
            session = ResearchSession(
                session_id=f"session-{i}",
                query=f"Query {i}",
                domain="academic",
                privacy_mode="cloud_allowed",
                status="completed",
                facts=[{"claim": f"Fact {i}", "confidence": 0.9}],
                sources=[{"url": f"https://example.com/{i}", "title": f"Source {i}"}],
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )
            await research_memory.save_session(session)

        stats = await research_memory.get_statistics()
        assert stats.total_sessions == 3
        assert stats.total_facts == 3
        assert stats.total_sources == 3
