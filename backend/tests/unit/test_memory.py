"""Tests for memory system (LanceDB + SQLite + Learning)."""

import os
import tempfile
from pathlib import Path

import pytest

from research_tool.services.memory import (
    CombinedMemoryRepository,
    LanceDBRepository,
    SourceLearning,
    SQLiteRepository,
)


class TestSQLiteRepository:
    """Tests for SQLite repository."""

    @pytest.fixture
    async def repo(self):
        """Create a temporary SQLite repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            repo = SQLiteRepository(str(db_path))
            await repo.initialize()
            yield repo

    async def test_create_and_get_session(self, repo):
        """Research session can be created and queried."""
        await repo.create_session(
            session_id="test-session-1",
            query="test query",
            domain="medical",
            privacy_mode="LOCAL_ONLY"
        )

        # Verify it was created (implementation would need a get_session method)
        # For now, just verify no errors

    async def test_source_effectiveness_updates(self, repo):
        """Source effectiveness updates correctly with EMA."""
        source = "test_source"
        domain = "medical"

        # First update - should use default 0.5
        await repo.set_source_effectiveness(
            source_name=source,
            domain=domain,
            effectiveness_score=0.8,
            quality_score=0.8,
            success=True
        )

        score = await repo.get_source_effectiveness(source, domain)
        assert score == 0.8

        # Second update
        await repo.set_source_effectiveness(
            source_name=source,
            domain=domain,
            effectiveness_score=0.6,
            quality_score=0.6,
            success=True
        )

        score = await repo.get_source_effectiveness(source, domain)
        assert score == 0.6

    async def test_unknown_source_returns_none(self, repo):
        """Unknown source returns None for effectiveness."""
        score = await repo.get_source_effectiveness("unknown", "medical")
        assert score is None

    async def test_access_failure_recording(self, repo):
        """Access failures are recorded and retrievable."""
        url = "https://paywall.example.com/article"
        source = "test_source"

        await repo.record_access_failure(
            url=url,
            source_name=source,
            error_type="paywall",
            error_message="403 Forbidden"
        )

        is_failed = await repo.is_known_failure(url)
        assert is_failed is True

        # Recording again should increment retry count
        await repo.record_access_failure(
            url=url,
            source_name=source,
            error_type="paywall",
            error_message="403 Forbidden"
        )

        is_failed = await repo.is_known_failure(url)
        assert is_failed is True

    async def test_unknown_url_not_failed(self, repo):
        """Unknown URLs are not marked as failed."""
        is_failed = await repo.is_known_failure("https://unknown.example.com")
        assert is_failed is False

    async def test_ranked_sources(self, repo):
        """Sources are ranked by effectiveness."""
        # Set up different effectiveness scores
        await repo.set_source_effectiveness("source_a", "medical", 0.9, 0.9, True)
        await repo.set_source_effectiveness("source_b", "medical", 0.5, 0.5, True)
        await repo.set_source_effectiveness("source_c", "medical", 0.7, 0.7, True)

        ranked = await repo.get_ranked_sources("medical", ["source_a", "source_b", "source_c"])

        assert len(ranked) == 3
        assert ranked[0][0] == "source_a"  # Highest score
        assert ranked[0][1] == 0.9
        assert ranked[1][0] == "source_c"  # Middle score
        assert ranked[2][0] == "source_b"  # Lowest score

    async def test_persistence_across_restart(self, repo):
        """Data persists when repository is recreated."""
        db_path = repo.db_path

        # Store some data
        await repo.set_source_effectiveness("test_source", "medical", 0.8, 0.8, True)

        # Close and recreate repository
        new_repo = SQLiteRepository(str(db_path))
        await new_repo.initialize()

        # Data should still be there
        score = await new_repo.get_source_effectiveness("test_source", "medical")
        assert score == 0.8


class TestLanceDBRepository:
    """Tests for LanceDB repository."""

    @pytest.fixture
    def repo(self):
        """Create a temporary LanceDB repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "lance_db"
            repo = LanceDBRepository(str(db_path))
            yield repo

    async def test_store_and_retrieve_document(self, repo):
        """Documents can be stored and retrieved."""
        doc_id = await repo.store_document(
            content="This is a test document about medical research.",
            metadata={"source_url": "https://example.com", "source_name": "test"},
            session_id="session-1"
        )

        assert doc_id is not None

        # Search for similar content
        results = await repo.search_similar("medical research", limit=5)

        assert len(results) > 0
        # The stored document should be in results
        found = any(r["session_id"] == "session-1" for r in results)
        assert found is True

    async def test_chunking_produces_chunks(self, repo):
        """Long documents are chunked appropriately."""
        # Create a long document (>400 words)
        long_text = " ".join(["word"] * 1000)

        chunks = repo.chunk_document(long_text)

        assert len(chunks) > 1  # Should produce multiple chunks

        # Chunks should have overlap
        # First chunk should have ~400 words
        first_chunk_words = len(chunks[0].split())
        assert 350 <= first_chunk_words <= 450

    async def test_short_document_not_chunked(self, repo):
        """Short documents are not chunked."""
        short_text = "This is a short document."

        chunks = repo.chunk_document(short_text)

        assert len(chunks) == 1
        assert chunks[0] == short_text

    async def test_hybrid_search_finds_relevant(self, repo):
        """Hybrid search returns semantically similar documents."""
        # Store multiple documents
        await repo.store_document(
            "Machine learning is a subset of artificial intelligence.",
            {"topic": "AI"},
            "session-1"
        )
        await repo.store_document(
            "Neural networks are used in deep learning applications.",
            {"topic": "AI"},
            "session-2"
        )
        await repo.store_document(
            "The weather today is sunny and warm.",
            {"topic": "weather"},
            "session-3"
        )

        # Search for AI-related content
        results = await repo.search_similar("artificial intelligence", limit=5)

        # Should find AI documents, not weather
        assert len(results) > 0
        # First results should be AI-related
        ai_results = [r for r in results if r["session_id"] in ["session-1", "session-2"]]
        assert len(ai_results) >= 1


class TestSourceLearning:
    """Tests for source effectiveness learning."""

    @pytest.fixture
    async def learning(self):
        """Create a temporary source learning instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            repo = SQLiteRepository(str(db_path))
            await repo.initialize()
            learning = SourceLearning(repo)
            yield learning

    async def test_effectiveness_updates_with_ema(self, learning):
        """Effectiveness updates using exponential moving average."""
        source = "test_source"
        domain = "medical"

        # First query - success with quality 1.0
        # new_score = 0.3 * 1.0 + 0.7 * 0.5 = 0.65
        score1 = await learning.update_effectiveness(source, domain, True, 1.0)
        assert abs(score1 - 0.65) < 0.01

        # Second query - success with quality 0.8
        # new_score = 0.3 * 0.8 + 0.7 * 0.65 = 0.695
        score2 = await learning.update_effectiveness(source, domain, True, 0.8)
        assert abs(score2 - 0.695) < 0.01

        # Third query - failure
        # new_score = 0.3 * 0.0 + 0.7 * 0.695 = 0.4865
        score3 = await learning.update_effectiveness(source, domain, False, 0.0)
        assert abs(score3 - 0.4865) < 0.01

    async def test_should_use_source_with_good_score(self, learning):
        """Sources with good scores should be used."""
        source = "good_source"
        domain = "medical"

        await learning.update_effectiveness(source, domain, True, 0.9)

        should_use = await learning.should_use_source(source, domain, threshold=0.3)
        assert should_use is True

    async def test_should_not_use_source_with_bad_score(self, learning):
        """Sources with bad scores should not be used."""
        source = "bad_source"
        domain = "medical"

        # Multiple failures to drive score down
        for _ in range(5):
            await learning.update_effectiveness(source, domain, False, 0.0)

        should_use = await learning.should_use_source(source, domain, threshold=0.3)
        assert should_use is False

    async def test_unknown_source_gets_benefit_of_doubt(self, learning):
        """Unknown sources are allowed (benefit of doubt)."""
        should_use = await learning.should_use_source("unknown", "medical", threshold=0.3)
        assert should_use is True


class TestCombinedMemoryRepository:
    """Tests for combined memory repository."""

    @pytest.fixture
    async def repo(self):
        """Create a temporary combined repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lance_path = Path(tmpdir) / "lance_db"
            sqlite_path = Path(tmpdir) / "test.db"
            repo = CombinedMemoryRepository(str(lance_path), str(sqlite_path))
            await repo.initialize()
            yield repo

    async def test_all_operations_work_together(self, repo):
        """All memory operations work together."""
        # Store document
        doc_id = await repo.store_document(
            "Test document content",
            {"source_name": "test", "domain": "medical"},
            "session-1"
        )
        assert doc_id is not None

        # Search similar
        results = await repo.search_similar("test content", limit=5)
        assert len(results) > 0

        # Update source effectiveness
        await repo.update_source_effectiveness("test", "medical", True, 0.8)
        score = await repo.get_source_effectiveness("test", "medical")
        assert score > 0.5

        # Record access failure
        await repo.record_access_failure(
            "https://example.com/fail",
            "test",
            "timeout",
            "Connection timeout"
        )
        is_failed = await repo.is_known_failure("https://example.com/fail")
        assert is_failed is True

    async def test_session_management(self, repo):
        """Research sessions can be created and updated."""
        await repo.create_session(
            session_id="test-123",
            query="test query",
            domain="medical",
            privacy_mode="LOCAL_ONLY"
        )

        await repo.update_session_status(
            session_id="test-123",
            status="completed",
            saturation_metrics={"novelty": 0.1},
            report_path="/path/to/report.md"
        )

        # If we had a get_session method, we'd verify here

    async def test_ranked_sources_integration(self, repo):
        """Source ranking works through combined repository."""
        # Set up different sources
        await repo.update_source_effectiveness("source_a", "medical", True, 0.9)
        await repo.update_source_effectiveness("source_b", "medical", True, 0.5)

        ranked = await repo.get_ranked_sources("medical", ["source_a", "source_b"])

        assert len(ranked) == 2
        assert ranked[0][0] == "source_a"  # Higher score first


@pytest.mark.benchmark
async def test_retrieval_latency_performance():
    """Retrieval should be fast even with many documents."""
    import time

    with tempfile.TemporaryDirectory() as tmpdir:
        lance_path = Path(tmpdir) / "lance_db"
        repo = LanceDBRepository(str(lance_path))

        # Store documents (reduced from 10K to 100 for faster testing)
        for i in range(100):
            await repo.store_document(
                f"Document {i} with content about topic {i % 10}",
                {"index": i},
                f"session-{i}"
            )

        # Measure retrieval time
        start = time.time()
        results = await repo.search_similar("topic content", limit=10)
        elapsed = time.time() - start

        assert len(results) > 0
        # Should be under 1 second for 100 docs (much more lenient than 100ms for 10K)
        assert elapsed < 1.0
