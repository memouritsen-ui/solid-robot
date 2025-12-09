"""Tests for agent decision logic."""

from research_tool.agent.decisions.clarification import (
    extract_ambiguous_terms,
    should_ask_for_clarification,
)
from research_tool.agent.decisions.source_selector import (
    select_sources_for_query,
    should_skip_source,
)
from research_tool.models.domain import DomainConfiguration


class TestSourceSelector:
    """Test suite for source selection decision tree."""

    def test_select_sources_with_domain_config(self) -> None:
        """select_sources_for_query uses domain config when available."""
        domain_config = DomainConfiguration.for_medical()
        effectiveness = {"pubmed": 0.9, "semantic_scholar": 0.8}

        sources = select_sources_for_query(
            query="test query",
            domain="medical",
            domain_config=domain_config,
            source_effectiveness=effectiveness
        )

        # Should include primary sources (pubmed, semantic_scholar)
        assert "pubmed" in sources
        assert "semantic_scholar" in sources

    def test_select_sources_orders_by_effectiveness(self) -> None:
        """select_sources_for_query orders sources by priority * effectiveness."""
        domain_config = DomainConfiguration.for_medical()
        # Higher effectiveness for semantic_scholar
        effectiveness = {"pubmed": 0.5, "semantic_scholar": 0.9}

        sources = select_sources_for_query(
            query="test query",
            domain="medical",
            domain_config=domain_config,
            source_effectiveness=effectiveness
        )

        # semantic_scholar (1.0 * 0.9 = 0.9) should come before pubmed (1.0 * 0.5 = 0.5)
        assert sources.index("semantic_scholar") < sources.index("pubmed")

    def test_select_sources_skips_known_failures(self) -> None:
        """select_sources_for_query skips sources in known_failures set."""
        domain_config = DomainConfiguration.for_medical()
        known_failures = {"pubmed"}

        sources = select_sources_for_query(
            query="test query",
            domain="medical",
            domain_config=domain_config,
            known_failures=known_failures
        )

        # Should not include pubmed
        assert "pubmed" not in sources
        # Should still include semantic_scholar
        assert "semantic_scholar" in sources

    def test_select_sources_for_novel_domain(self) -> None:
        """select_sources_for_query uses general sources for novel domain."""
        sources = select_sources_for_query(
            query="completely novel topic",
            domain=None,
            domain_config=None
        )

        # Should include general-purpose sources
        assert "tavily" in sources
        assert "exa" in sources
        assert "brave" in sources

    def test_select_sources_excludes_domain_excluded(self) -> None:
        """select_sources_for_query excludes sources in domain config excluded list."""
        domain_config = DomainConfiguration.for_medical()
        # Medical domain excludes wikipedia

        sources = select_sources_for_query(
            query="test query",
            domain="medical",
            domain_config=domain_config
        )

        # Should not include wikipedia (even if it was in primary/secondary)
        assert "wikipedia" not in sources

    def test_should_skip_source_with_matching_pattern(self) -> None:
        """should_skip_source returns True for matching failure pattern.

        Note: Phase 4 uses simple substring matching, not wildcards.
        Phase 5 will add proper glob pattern matching.
        """
        known_failures = {
            "pubmed": {"arxiv.org"}
        }

        result = should_skip_source(
            source_name="pubmed",
            url_pattern="arxiv.org/paper.pdf",
            known_failures=known_failures
        )

        assert result is True

    def test_should_skip_source_without_matching_pattern(self) -> None:
        """should_skip_source returns False when pattern doesn't match."""
        known_failures = {
            "pubmed": {"*.pdf"}
        }

        result = should_skip_source(
            source_name="pubmed",
            url_pattern="example.com/article",
            known_failures=known_failures
        )

        assert result is False

    def test_should_skip_source_no_known_failures(self) -> None:
        """should_skip_source returns False when no known failures."""
        result = should_skip_source(
            source_name="pubmed",
            url_pattern="example.com",
            known_failures=None
        )

        assert result is False


class TestClarification:
    """Test suite for clarification decision tree."""

    def test_should_ask_when_domain_unknown_and_no_default(self) -> None:
        """should_ask_for_clarification asks when domain unknown and no default."""
        # Short query with no domain
        should_ask, question = should_ask_for_clarification(
            query="test",  # Very short, no reasonable default
            domain=None,
            scope_clear=True,
            has_ambiguous_terms=False,
            clarification_count=0
        )

        assert should_ask is True
        assert "field or industry" in question.lower()

    def test_should_not_ask_when_domain_recognized(self) -> None:
        """should_ask_for_clarification doesn't ask when domain is clear."""
        should_ask, question = should_ask_for_clarification(
            query="medical research on cancer treatments",
            domain="medical",
            scope_clear=True,
            has_ambiguous_terms=False,
            clarification_count=0
        )

        assert should_ask is False
        assert question is None

    def test_should_ask_when_scope_unclear_and_not_acceptable(self) -> None:
        """should_ask_for_clarification asks when scope unclear and narrow needed."""
        # Very long query needs narrow scope
        long_query = " ".join(["word"] * 20)

        should_ask, question = should_ask_for_clarification(
            query=long_query,
            domain="medical",
            scope_clear=False,
            has_ambiguous_terms=False,
            clarification_count=0
        )

        assert should_ask is True
        assert question is not None

    def test_should_ask_when_ambiguous_and_costly(self) -> None:
        """should_ask_for_clarification asks when ambiguous in high-cost domain."""
        should_ask, question = should_ask_for_clarification(
            query="treatment options",
            domain="medical",  # High-cost domain
            scope_clear=True,
            has_ambiguous_terms=True,
            clarification_count=0
        )

        # Medical domain + ambiguity = should ask
        assert should_ask is True

    def test_should_not_ask_after_max_clarifications(self) -> None:
        """should_ask_for_clarification stops after 2 clarifications (MAX)."""
        should_ask, question = should_ask_for_clarification(
            query="test",
            domain=None,
            scope_clear=False,
            has_ambiguous_terms=True,
            clarification_count=2  # Already asked twice
        )

        # Should stop asking after 2 clarifications
        assert should_ask is False
        assert question is None

    def test_extract_ambiguous_terms_finds_vague_words(self) -> None:
        """extract_ambiguous_terms identifies vague pronouns."""
        ambiguous = extract_ambiguous_terms("What does that mean?")

        assert "that" in ambiguous

    def test_extract_ambiguous_terms_empty_for_clear_query(self) -> None:
        """extract_ambiguous_terms returns empty list for clear query."""
        ambiguous = extract_ambiguous_terms("cancer treatment options")

        assert len(ambiguous) == 0


class TestDecisionIntegration:
    """Integration tests for decision logic."""

    def test_medical_domain_selects_academic_sources(self) -> None:
        """Medical domain prioritizes academic sources."""
        domain_config = DomainConfiguration.for_medical()

        sources = select_sources_for_query(
            query="cancer research",
            domain="medical",
            domain_config=domain_config
        )

        # First few sources should be academic
        first_three = sources[:3]
        academic_sources = {"pubmed", "semantic_scholar", "arxiv"}

        # At least 2 of first 3 should be academic
        academic_count = sum(1 for s in first_three if s in academic_sources)
        assert academic_count >= 2

    def test_competitive_intelligence_selects_web_sources(self) -> None:
        """Competitive intelligence domain prioritizes web sources."""
        domain_config = DomainConfiguration.for_competitive_intelligence()

        sources = select_sources_for_query(
            query="company funding",
            domain="competitive_intelligence",
            domain_config=domain_config
        )

        # Should include web search providers
        assert "tavily" in sources
        assert "exa" in sources

    def test_clarification_workflow_for_vague_query(self) -> None:
        """Vague query triggers clarification then proceeds."""
        # First clarification - no domain
        should_ask_1, q1 = should_ask_for_clarification(
            query="it",
            domain=None,
            scope_clear=True,
            has_ambiguous_terms=True,
            clarification_count=0
        )
        assert should_ask_1 is True

        # Second clarification - scope unclear but query is short (3 words)
        # Short queries (<= 15 words) use broad scope, so won't ask
        should_ask_2, q2 = should_ask_for_clarification(
            query="very long detailed research query on information technology "
                  "systems architecture patterns best practices modern approaches "
                  "implementation strategies",  # >15 words
            domain="academic",
            scope_clear=False,
            has_ambiguous_terms=False,
            clarification_count=1
        )
        assert should_ask_2 is True

        # Third attempt - should proceed (max 2 clarifications)
        should_ask_3, q3 = should_ask_for_clarification(
            query="research on information technology",
            domain="academic",
            scope_clear=True,
            has_ambiguous_terms=False,
            clarification_count=2
        )
        assert should_ask_3 is False
