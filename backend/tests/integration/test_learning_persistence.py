"""Integration tests for learning persistence across research sessions.

Task #228: Test that learning persists to next research.

These tests use REAL SQLite databases (temp files) to verify:
1. Learning affects source ranking within same session
2. Learning persists to disk and survives restart
3. Multiple domains persist independently
4. Effectiveness influences future source ranking
"""

import tempfile

import pytest

from research_tool.services.memory.learning import PostResearchLearner, SourceLearning
from research_tool.services.memory.sqlite_repo import SQLiteRepository


class TestLearningPersistence:
    """Integration tests for learning persistence."""

    @pytest.fixture
    async def temp_db_path(self) -> str:
        """Create temporary database file path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            return f.name

    @pytest.fixture
    async def sqlite_repo(self, temp_db_path: str) -> SQLiteRepository:
        """Create real SQLite repository with temp database."""
        repo = SQLiteRepository(db_path=temp_db_path)
        await repo.initialize()
        return repo

    @pytest.fixture
    def source_learning(self, sqlite_repo: SQLiteRepository) -> SourceLearning:
        """Create SourceLearning with real repo."""
        return SourceLearning(sqlite_repo)

    @pytest.fixture
    def learner(self, source_learning: SourceLearning) -> PostResearchLearner:
        """Create PostResearchLearner instance."""
        return PostResearchLearner(source_learning)

    @pytest.mark.asyncio
    async def test_learning_affects_source_ranking_same_session(
        self,
        sqlite_repo: SQLiteRepository,
        source_learning: SourceLearning,
        learner: PostResearchLearner,
    ) -> None:
        """Test that learning from session A affects ranking in session B (same process).

        Scenario:
        1. Research session A: pubmed performs well, brave performs poorly
        2. Research session B: Check that pubmed is ranked higher than brave
        """
        # Session A: pubmed gets high-quality facts, brave gets nothing
        await learner.trigger_learning({
            "domain": "medical",
            "sources_queried": ["pubmed", "brave"],
            "facts_extracted": [
                {"source": "pubmed", "confidence": 0.95},
                {"source": "pubmed", "confidence": 0.90},
                {"source": "pubmed", "confidence": 0.85},
                # brave produced no useful facts
            ],
        })

        # Session B: Check rankings
        rankings = await source_learning.get_ranked_sources(
            domain="medical",
            available_sources=["pubmed", "brave", "tavily"]
        )

        # pubmed should be ranked higher than brave
        ranking_dict = dict(rankings)

        assert ranking_dict["pubmed"] > ranking_dict["brave"], (
            f"pubmed ({ranking_dict['pubmed']:.3f}) should rank higher than "
            f"brave ({ranking_dict['brave']:.3f}) after learning"
        )

    @pytest.mark.asyncio
    async def test_learning_persists_to_disk(
        self,
        temp_db_path: str,
    ) -> None:
        """Test that learning persists to disk and can be read by new connection.

        Scenario:
        1. Create repo, write learning data, close
        2. Create NEW repo instance with same path
        3. Verify data is still there
        """
        # First connection: write data
        repo1 = SQLiteRepository(db_path=temp_db_path)
        await repo1.initialize()
        learning1 = SourceLearning(repo1)
        learner1 = PostResearchLearner(learning1)

        await learner1.trigger_learning({
            "domain": "academic",
            "sources_queried": ["arxiv", "semantic_scholar"],
            "facts_extracted": [
                {"source": "arxiv", "confidence": 0.9},
                {"source": "arxiv", "confidence": 0.85},
            ],
        })

        # Verify data was written
        score_before = await repo1.get_source_effectiveness("arxiv", "academic")
        assert score_before is not None, "Score should exist after learning"

        # Second connection: read data (simulates restart)
        repo2 = SQLiteRepository(db_path=temp_db_path)
        await repo2.initialize()

        score_after = await repo2.get_source_effectiveness("arxiv", "academic")

        assert score_after is not None, "Score should persist across connections"
        assert score_after == pytest.approx(score_before, rel=0.01), (
            f"Score should be same: {score_before} vs {score_after}"
        )

    @pytest.mark.asyncio
    async def test_multiple_domains_persist_independently(
        self,
        sqlite_repo: SQLiteRepository,
        source_learning: SourceLearning,
        learner: PostResearchLearner,
    ) -> None:
        """Test that learning for different domains is stored independently.

        Scenario:
        1. pubmed performs well in medical domain
        2. pubmed performs poorly in competitive_intelligence domain
        3. Rankings should differ by domain
        """
        # Medical: pubmed does well
        await learner.trigger_learning({
            "domain": "medical",
            "sources_queried": ["pubmed", "brave"],
            "facts_extracted": [
                {"source": "pubmed", "confidence": 0.95},
                {"source": "pubmed", "confidence": 0.90},
            ],
        })

        # Competitive Intelligence: pubmed does poorly, brave does well
        await learner.trigger_learning({
            "domain": "competitive_intelligence",
            "sources_queried": ["pubmed", "brave"],
            "facts_extracted": [
                {"source": "brave", "confidence": 0.9},
                {"source": "brave", "confidence": 0.85},
                # pubmed produced nothing useful for CI
            ],
        })

        # Check rankings per domain
        medical_rankings = await source_learning.get_ranked_sources(
            domain="medical",
            available_sources=["pubmed", "brave"]
        )
        ci_rankings = await source_learning.get_ranked_sources(
            domain="competitive_intelligence",
            available_sources=["pubmed", "brave"]
        )

        medical_dict = dict(medical_rankings)
        ci_dict = dict(ci_rankings)

        # In medical: pubmed > brave
        assert medical_dict["pubmed"] > medical_dict["brave"], (
            f"Medical: pubmed ({medical_dict['pubmed']:.3f}) should beat "
            f"brave ({medical_dict['brave']:.3f})"
        )

        # In CI: brave > pubmed
        assert ci_dict["brave"] > ci_dict["pubmed"], (
            f"CI: brave ({ci_dict['brave']:.3f}) should beat "
            f"pubmed ({ci_dict['pubmed']:.3f})"
        )

    @pytest.mark.asyncio
    async def test_effectiveness_influences_future_ranking(
        self,
        sqlite_repo: SQLiteRepository,
        source_learning: SourceLearning,
        learner: PostResearchLearner,
    ) -> None:
        """Test that accumulated effectiveness influences future source selection.

        Scenario:
        1. Multiple sessions where arxiv consistently outperforms semantic_scholar
        2. Verify arxiv's score increases and exceeds semantic_scholar
        """
        # Session 1: arxiv good, semantic_scholar mediocre
        await learner.trigger_learning({
            "domain": "academic",
            "sources_queried": ["arxiv", "semantic_scholar"],
            "facts_extracted": [
                {"source": "arxiv", "confidence": 0.9},
                {"source": "semantic_scholar", "confidence": 0.5},
            ],
        })

        # Session 2: arxiv still good, semantic_scholar still mediocre
        await learner.trigger_learning({
            "domain": "academic",
            "sources_queried": ["arxiv", "semantic_scholar"],
            "facts_extracted": [
                {"source": "arxiv", "confidence": 0.85},
                {"source": "semantic_scholar", "confidence": 0.4},
            ],
        })

        # Session 3: arxiv excellent, semantic_scholar poor
        await learner.trigger_learning({
            "domain": "academic",
            "sources_queried": ["arxiv", "semantic_scholar"],
            "facts_extracted": [
                {"source": "arxiv", "confidence": 0.95},
                {"source": "semantic_scholar", "confidence": 0.3},
            ],
        })

        score3_arxiv = await sqlite_repo.get_source_effectiveness("arxiv", "academic")
        score3_ss = await sqlite_repo.get_source_effectiveness(
            "semantic_scholar", "academic"
        )

        # Verify arxiv maintains higher score than semantic_scholar
        assert score3_arxiv > score3_ss, (
            f"After 3 sessions, arxiv ({score3_arxiv:.3f}) should beat "
            f"semantic_scholar ({score3_ss:.3f})"
        )

        # Verify should_use_source reflects learning
        should_use_arxiv = await source_learning.should_use_source(
            "arxiv", "academic", threshold=0.3
        )
        assert should_use_arxiv is True, "arxiv should be recommended"
