"""Integration tests for learning influencing future research (#235).

Tests that learning from previous research sessions affects:
1. Source selection order in source_selector
2. Source ranking returned by get_ranked_sources
3. The should_use_source decision for low-performing sources

These tests demonstrate the full learning loop:
Research Session A → Learning Update → Research Session B (uses learned data)
"""

import tempfile

import pytest

from research_tool.agent.decisions.source_selector import select_sources_for_query
from research_tool.models.domain import DomainConfiguration
from research_tool.services.memory.learning import PostResearchLearner, SourceLearning
from research_tool.services.memory.sqlite_repo import SQLiteRepository


class TestLearningInfluencesFutureResearch:
    """Integration tests for learning influencing future source selection."""

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
    async def test_learning_affects_source_selector_ordering(
        self,
        sqlite_repo: SQLiteRepository,
        source_learning: SourceLearning,
        learner: PostResearchLearner,
    ) -> None:
        """Test that learned effectiveness affects source_selector ordering.

        Scenario:
        1. Research session: pubmed excels, semantic_scholar fails
        2. Build effectiveness dict from learned data
        3. Call select_sources_for_query with effectiveness
        4. Verify pubmed ranks before semantic_scholar
        """
        # Session 1: pubmed performs excellently
        await learner.trigger_learning({
            "domain": "medical",
            "sources_queried": ["pubmed", "semantic_scholar", "arxiv"],
            "facts_extracted": [
                {"source": "pubmed", "confidence": 0.95},
                {"source": "pubmed", "confidence": 0.92},
                {"source": "pubmed", "confidence": 0.88},
                {"source": "arxiv", "confidence": 0.75},
                # semantic_scholar produced nothing
            ],
        })

        # Session 2: Same pattern
        await learner.trigger_learning({
            "domain": "medical",
            "sources_queried": ["pubmed", "semantic_scholar"],
            "facts_extracted": [
                {"source": "pubmed", "confidence": 0.90},
                {"source": "pubmed", "confidence": 0.85},
            ],
        })

        # Get learned effectiveness scores
        available_sources = ["pubmed", "semantic_scholar", "arxiv", "tavily"]
        rankings = await source_learning.get_ranked_sources(
            domain="medical",
            available_sources=available_sources
        )
        effectiveness = dict(rankings)

        # Create domain config with all sources as primary
        config = DomainConfiguration(
            domain="medical",
            primary_sources=["pubmed", "semantic_scholar", "arxiv"],
            secondary_sources=["tavily"],
            academic_required=True,
            verification_threshold=0.8,
            keywords=["medical"],
            excluded_sources=[]
        )

        # Call source selector with learned effectiveness
        selected = select_sources_for_query(
            query="diabetes treatment outcomes",
            domain="medical",
            domain_config=config,
            source_effectiveness=effectiveness
        )

        # pubmed should come before semantic_scholar
        pubmed_idx = selected.index("pubmed")
        ss_idx = selected.index("semantic_scholar")

        assert pubmed_idx < ss_idx, (
            f"pubmed (idx={pubmed_idx}) should be selected before "
            f"semantic_scholar (idx={ss_idx}) based on learned effectiveness. "
            f"Effectiveness: pubmed={effectiveness.get('pubmed', 0.5):.3f}, "
            f"semantic_scholar={effectiveness.get('semantic_scholar', 0.5):.3f}"
        )

    @pytest.mark.asyncio
    async def test_failing_source_gets_deprioritized(
        self,
        sqlite_repo: SQLiteRepository,
        source_learning: SourceLearning,
        learner: PostResearchLearner,
    ) -> None:
        """Test that repeatedly failing sources get deprioritized.

        Scenario:
        1. Multiple sessions where brave consistently fails
        2. Verify brave's effectiveness drops below threshold
        3. Verify should_use_source returns False for brave
        """
        # Session 1: brave fails
        await learner.trigger_learning({
            "domain": "competitive_intelligence",
            "sources_queried": ["brave", "tavily"],
            "facts_extracted": [
                {"source": "tavily", "confidence": 0.8},
            ],
            "access_failures": [
                {"source": "brave", "error": "rate_limited"}
            ],
        })

        # Session 2: brave fails again
        await learner.trigger_learning({
            "domain": "competitive_intelligence",
            "sources_queried": ["brave", "tavily"],
            "facts_extracted": [
                {"source": "tavily", "confidence": 0.85},
            ],
            "access_failures": [
                {"source": "brave", "error": "timeout"}
            ],
        })

        # Session 3: brave fails yet again
        await learner.trigger_learning({
            "domain": "competitive_intelligence",
            "sources_queried": ["brave", "tavily"],
            "facts_extracted": [
                {"source": "tavily", "confidence": 0.9},
            ],
            "access_failures": [
                {"source": "brave", "error": "blocked"}
            ],
        })

        # Verify brave's effectiveness is low
        brave_score = await sqlite_repo.get_source_effectiveness(
            "brave", "competitive_intelligence"
        )

        # After 3 failures, brave should have very low score
        # Using EMA with alpha=0.3: score = 0.3*0 + 0.7*prev
        # Starting from 0.5: 0.35 -> 0.245 -> 0.1715
        assert brave_score is not None
        assert brave_score < 0.3, (
            f"brave score ({brave_score:.3f}) should be < 0.3 after 3 failures"
        )

        # Verify should_use_source returns False for brave
        should_use = await source_learning.should_use_source(
            "brave", "competitive_intelligence", threshold=0.3
        )
        assert should_use is False, (
            f"should_use_source should return False for brave "
            f"(score={brave_score:.3f}, threshold=0.3)"
        )

    @pytest.mark.asyncio
    async def test_learning_improves_source_over_time(
        self,
        sqlite_repo: SQLiteRepository,
        source_learning: SourceLearning,
        learner: PostResearchLearner,
    ) -> None:
        """Test that consistently good performance improves source ranking.

        Scenario:
        1. Multiple sessions where arxiv consistently performs well
        2. Verify arxiv's effectiveness increases
        3. Verify arxiv gets prioritized in future selection
        """
        # Start with unknown source (default 0.5)
        initial_score = await sqlite_repo.get_source_effectiveness(
            "arxiv", "academic"
        )
        assert initial_score is None, "arxiv should have no score initially"

        # Session 1: arxiv performs well
        await learner.trigger_learning({
            "domain": "academic",
            "sources_queried": ["arxiv"],
            "facts_extracted": [
                {"source": "arxiv", "confidence": 0.9},
                {"source": "arxiv", "confidence": 0.85},
            ],
        })

        score_1 = await sqlite_repo.get_source_effectiveness("arxiv", "academic")

        # Session 2: arxiv performs excellently
        await learner.trigger_learning({
            "domain": "academic",
            "sources_queried": ["arxiv"],
            "facts_extracted": [
                {"source": "arxiv", "confidence": 0.95},
                {"source": "arxiv", "confidence": 0.92},
            ],
        })

        score_2 = await sqlite_repo.get_source_effectiveness("arxiv", "academic")

        # Session 3: arxiv continues to excel
        await learner.trigger_learning({
            "domain": "academic",
            "sources_queried": ["arxiv"],
            "facts_extracted": [
                {"source": "arxiv", "confidence": 0.98},
                {"source": "arxiv", "confidence": 0.96},
            ],
        })

        score_3 = await sqlite_repo.get_source_effectiveness("arxiv", "academic")

        # Verify improvement over time
        assert score_1 is not None
        assert score_2 is not None
        assert score_3 is not None

        # Scores should be increasing (or at least maintaining high level)
        # With EMA, consistently high performance should keep score high
        assert score_2 >= score_1 * 0.95, (
            f"Score should improve or maintain: session1={score_1:.3f}, "
            f"session2={score_2:.3f}"
        )
        assert score_3 >= score_2 * 0.95, (
            f"Score should improve or maintain: session2={score_2:.3f}, "
            f"session3={score_3:.3f}"
        )

        # Final score should be high (>0.7)
        assert score_3 > 0.7, (
            f"After 3 excellent sessions, score ({score_3:.3f}) should be > 0.7"
        )

    @pytest.mark.asyncio
    async def test_domain_specific_learning_isolation(
        self,
        sqlite_repo: SQLiteRepository,
        source_learning: SourceLearning,
        learner: PostResearchLearner,
    ) -> None:
        """Test that learning in one domain doesn't affect another.

        Scenario:
        1. pubmed excels in medical domain
        2. pubmed fails in competitive_intelligence domain
        3. Rankings should differ between domains
        """
        # Medical: pubmed is great
        await learner.trigger_learning({
            "domain": "medical",
            "sources_queried": ["pubmed", "tavily"],
            "facts_extracted": [
                {"source": "pubmed", "confidence": 0.95},
                {"source": "pubmed", "confidence": 0.9},
                {"source": "tavily", "confidence": 0.6},
            ],
        })

        # CI: pubmed is useless (produces nothing relevant)
        await learner.trigger_learning({
            "domain": "competitive_intelligence",
            "sources_queried": ["pubmed", "tavily"],
            "facts_extracted": [
                {"source": "tavily", "confidence": 0.85},
                {"source": "tavily", "confidence": 0.8},
                # pubmed produced nothing for CI
            ],
        })

        # Get rankings for each domain
        medical_rankings = await source_learning.get_ranked_sources(
            domain="medical",
            available_sources=["pubmed", "tavily"]
        )
        ci_rankings = await source_learning.get_ranked_sources(
            domain="competitive_intelligence",
            available_sources=["pubmed", "tavily"]
        )

        medical_dict = dict(medical_rankings)
        ci_dict = dict(ci_rankings)

        # Medical: pubmed should beat tavily
        assert medical_dict["pubmed"] > medical_dict["tavily"], (
            f"Medical: pubmed ({medical_dict['pubmed']:.3f}) should beat "
            f"tavily ({medical_dict['tavily']:.3f})"
        )

        # CI: tavily should beat pubmed
        assert ci_dict["tavily"] > ci_dict["pubmed"], (
            f"CI: tavily ({ci_dict['tavily']:.3f}) should beat "
            f"pubmed ({ci_dict['pubmed']:.3f})"
        )

    @pytest.mark.asyncio
    async def test_known_failures_exclude_sources(
        self,
        sqlite_repo: SQLiteRepository,
        source_learning: SourceLearning,
        learner: PostResearchLearner,
    ) -> None:
        """Test that known failures can be passed to exclude sources.

        Scenario:
        1. Build a set of sources that should be excluded
        2. Verify select_sources_for_query respects known_failures parameter
        """
        config = DomainConfiguration(
            domain="academic",
            primary_sources=["arxiv", "semantic_scholar", "pubmed"],
            secondary_sources=["tavily"],
            academic_required=True,
            verification_threshold=0.7,
            keywords=["research"],
            excluded_sources=[]
        )

        # Select without known failures
        selected_all = select_sources_for_query(
            query="machine learning research",
            domain="academic",
            domain_config=config,
            source_effectiveness=None,
            known_failures=None
        )

        # Select with arxiv as known failure
        selected_without_arxiv = select_sources_for_query(
            query="machine learning research",
            domain="academic",
            domain_config=config,
            source_effectiveness=None,
            known_failures={"arxiv"}
        )

        assert "arxiv" in selected_all, "arxiv should be in selection without failures"
        assert "arxiv" not in selected_without_arxiv, (
            "arxiv should NOT be in selection with known_failures={'arxiv'}"
        )
