"""Tests for post-research learning trigger.

TDD: Writing tests FIRST before implementation.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from research_tool.services.memory.learning import PostResearchLearner, SourceLearning


class TestPostResearchLearner:
    """Tests for PostResearchLearner class."""

    @pytest.fixture
    def mock_sqlite_repo(self) -> MagicMock:
        """Create mock SQLite repository."""
        repo = MagicMock()
        repo.get_source_effectiveness = AsyncMock(return_value=0.5)
        repo.set_source_effectiveness = AsyncMock()
        return repo

    @pytest.fixture
    def source_learning(self, mock_sqlite_repo: MagicMock) -> SourceLearning:
        """Create SourceLearning with mock repo."""
        return SourceLearning(mock_sqlite_repo)

    @pytest.fixture
    def learner(self, source_learning: SourceLearning) -> PostResearchLearner:
        """Create PostResearchLearner instance."""
        return PostResearchLearner(source_learning)

    @pytest.mark.asyncio
    async def test_trigger_updates_source_effectiveness(
        self, learner: PostResearchLearner, mock_sqlite_repo: MagicMock
    ) -> None:
        """Test that trigger_learning updates source effectiveness."""
        research_result = {
            "domain": "medical",
            "sources_queried": ["pubmed", "semantic_scholar"],
            "facts_extracted": [
                {"source": "pubmed", "confidence": 0.9},
                {"source": "semantic_scholar", "confidence": 0.7},
            ],
        }

        await learner.trigger_learning(research_result)

        # Should have called set_source_effectiveness for each source
        assert mock_sqlite_repo.set_source_effectiveness.call_count >= 2

    @pytest.mark.asyncio
    async def test_calculates_quality_from_facts(
        self, learner: PostResearchLearner
    ) -> None:
        """Test quality score calculation from extracted facts."""
        facts = [
            {"source": "pubmed", "confidence": 0.9},
            {"source": "pubmed", "confidence": 0.8},
            {"source": "pubmed", "confidence": 0.7},
        ]

        quality = learner.calculate_source_quality("pubmed", facts)

        # Average of 0.9, 0.8, 0.7 = 0.8
        assert quality == pytest.approx(0.8, rel=0.01)

    @pytest.mark.asyncio
    async def test_handles_empty_facts(
        self, learner: PostResearchLearner
    ) -> None:
        """Test quality calculation with no facts for source."""
        facts = [
            {"source": "other_source", "confidence": 0.9},
        ]

        quality = learner.calculate_source_quality("pubmed", facts)

        # No facts from pubmed = 0.0 quality (failed to produce useful results)
        assert quality == 0.0

    @pytest.mark.asyncio
    async def test_marks_failed_sources(
        self, learner: PostResearchLearner, mock_sqlite_repo: MagicMock
    ) -> None:
        """Test that sources with no results are marked as failed."""
        research_result = {
            "domain": "medical",
            "sources_queried": ["pubmed", "failing_source"],
            "facts_extracted": [
                {"source": "pubmed", "confidence": 0.9},
                # No facts from failing_source
            ],
        }

        await learner.trigger_learning(research_result)

        # Should update failing_source with success=False
        calls = mock_sqlite_repo.set_source_effectiveness.call_args_list
        failing_calls = [c for c in calls if "failing_source" in str(c)]
        assert len(failing_calls) > 0

    @pytest.mark.asyncio
    async def test_respects_domain_context(
        self, learner: PostResearchLearner, mock_sqlite_repo: MagicMock
    ) -> None:
        """Test that learning is domain-specific."""
        research_result = {
            "domain": "competitive_intelligence",
            "sources_queried": ["brave", "tavily"],
            "facts_extracted": [
                {"source": "brave", "confidence": 0.8},
            ],
        }

        await learner.trigger_learning(research_result)

        # All calls should use the correct domain
        for call in mock_sqlite_repo.set_source_effectiveness.call_args_list:
            if len(call[1]) > 0:  # keyword args
                assert call[1].get("domain") == "competitive_intelligence"

    @pytest.mark.asyncio
    async def test_handles_missing_domain(
        self, learner: PostResearchLearner
    ) -> None:
        """Test graceful handling when domain is missing."""
        research_result = {
            "sources_queried": ["pubmed"],
            "facts_extracted": [],
        }

        # Should not raise
        await learner.trigger_learning(research_result)

    @pytest.mark.asyncio
    async def test_handles_empty_sources_queried(
        self, learner: PostResearchLearner, mock_sqlite_repo: MagicMock
    ) -> None:
        """Test handling of empty sources list."""
        research_result = {
            "domain": "medical",
            "sources_queried": [],
            "facts_extracted": [],
        }

        await learner.trigger_learning(research_result)

        # Should not call set_source_effectiveness at all
        assert mock_sqlite_repo.set_source_effectiveness.call_count == 0

    @pytest.mark.asyncio
    async def test_normalizes_source_names(
        self, learner: PostResearchLearner
    ) -> None:
        """Test that source names are normalized."""
        facts = [
            {"source": "PubMed", "confidence": 0.9},
            {"source": "PUBMED", "confidence": 0.8},
            {"source": "pubmed", "confidence": 0.7},
        ]

        quality = learner.calculate_source_quality("pubmed", facts)

        # All should be treated as same source
        assert quality == pytest.approx(0.8, rel=0.01)

    @pytest.mark.asyncio
    async def test_returns_learning_summary(
        self, learner: PostResearchLearner
    ) -> None:
        """Test that trigger_learning returns a summary."""
        research_result = {
            "domain": "medical",
            "sources_queried": ["pubmed"],
            "facts_extracted": [
                {"source": "pubmed", "confidence": 0.9},
            ],
        }

        summary = await learner.trigger_learning(research_result)

        assert "sources_updated" in summary
        assert summary["sources_updated"] >= 1

    @pytest.mark.asyncio
    async def test_handles_access_failures_list(
        self, learner: PostResearchLearner, mock_sqlite_repo: MagicMock
    ) -> None:
        """Test that access_failures from state are used."""
        research_result = {
            "domain": "medical",
            "sources_queried": ["pubmed", "arxiv"],
            "facts_extracted": [{"source": "pubmed", "confidence": 0.9}],
            "access_failures": [
                {"source": "arxiv", "error": "rate_limited"},
            ],
        }

        await learner.trigger_learning(research_result)

        # arxiv should be marked as failed due to access_failures
        calls = mock_sqlite_repo.set_source_effectiveness.call_args_list
        arxiv_calls = [c for c in calls if "arxiv" in str(c)]
        assert len(arxiv_calls) > 0


class TestSourceLearningIntegration:
    """Integration tests for SourceLearning with PostResearchLearner."""

    @pytest.fixture
    def mock_sqlite_repo(self) -> MagicMock:
        """Create mock SQLite repository with tracking."""
        repo = MagicMock()
        repo.effectiveness_store: dict[tuple[str, str], float] = {}

        async def get_effectiveness(
            source_name: str, domain: str | None
        ) -> float | None:
            key = (source_name.lower(), domain or "default")
            return repo.effectiveness_store.get(key)

        async def set_effectiveness(
            source_name: str,
            domain: str,
            effectiveness_score: float,
            quality_score: float | None = None,
            success: bool = True,
        ) -> None:
            key = (source_name.lower(), domain)
            repo.effectiveness_store[key] = effectiveness_score

        repo.get_source_effectiveness = AsyncMock(side_effect=get_effectiveness)
        repo.set_source_effectiveness = AsyncMock(side_effect=set_effectiveness)
        return repo

    @pytest.mark.asyncio
    async def test_multiple_research_sessions_improve_ranking(
        self, mock_sqlite_repo: MagicMock
    ) -> None:
        """Test that multiple sessions improve source ranking accuracy."""
        source_learning = SourceLearning(mock_sqlite_repo)
        learner = PostResearchLearner(source_learning)

        # Session 1: pubmed performs well
        await learner.trigger_learning({
            "domain": "medical",
            "sources_queried": ["pubmed", "brave"],
            "facts_extracted": [
                {"source": "pubmed", "confidence": 0.9},
                {"source": "pubmed", "confidence": 0.85},
            ],
        })

        # Session 2: pubmed still good, brave better
        await learner.trigger_learning({
            "domain": "medical",
            "sources_queried": ["pubmed", "brave"],
            "facts_extracted": [
                {"source": "pubmed", "confidence": 0.8},
                {"source": "brave", "confidence": 0.95},
            ],
        })

        # Both should have effectiveness scores now
        pubmed_score = mock_sqlite_repo.effectiveness_store.get(
            ("pubmed", "medical")
        )
        brave_score = mock_sqlite_repo.effectiveness_store.get(
            ("brave", "medical")
        )

        assert pubmed_score is not None
        assert brave_score is not None
