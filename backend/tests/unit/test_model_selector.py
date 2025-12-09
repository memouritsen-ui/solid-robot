"""Tests for ModelSelector - model selection based on privacy and complexity.

Tests ensure the critical privacy invariant: LOCAL_ONLY mode NEVER selects cloud models.
"""

import pytest

from research_tool.services.llm import ModelSelector, PrivacyMode, TaskComplexity


class TestModelSelectorPrivacy:
    """Tests for privacy mode enforcement."""

    def test_local_only_high_complexity_selects_local_powerful(self) -> None:
        """LOCAL_ONLY + HIGH → local-powerful."""
        selector = ModelSelector()
        result = selector.select(
            task_complexity=TaskComplexity.HIGH,
            privacy_mode=PrivacyMode.LOCAL_ONLY,
        )
        assert result.model == "local-powerful"
        assert result.privacy_compliant is True
        assert "cloud" not in result.model

    def test_local_only_medium_complexity_selects_local_fast(self) -> None:
        """LOCAL_ONLY + MEDIUM → local-fast."""
        selector = ModelSelector()
        result = selector.select(
            task_complexity=TaskComplexity.MEDIUM,
            privacy_mode=PrivacyMode.LOCAL_ONLY,
        )
        assert result.model == "local-fast"
        assert result.privacy_compliant is True

    def test_local_only_low_complexity_selects_local_fast(self) -> None:
        """LOCAL_ONLY + LOW → local-fast."""
        selector = ModelSelector()
        result = selector.select(
            task_complexity=TaskComplexity.LOW,
            privacy_mode=PrivacyMode.LOCAL_ONLY,
        )
        assert result.model == "local-fast"
        assert result.privacy_compliant is True

    def test_local_only_never_selects_cloud(self) -> None:
        """CRITICAL: LOCAL_ONLY should NEVER return a cloud model."""
        selector = ModelSelector()
        for complexity in TaskComplexity:
            result = selector.select(
                task_complexity=complexity,
                privacy_mode=PrivacyMode.LOCAL_ONLY,
            )
            assert "cloud" not in result.model, (
                f"LOCAL_ONLY + {complexity.name} selected cloud model: {result.model}"
            )
            assert result.privacy_compliant is True

    def test_local_only_raises_when_no_local_models(self) -> None:
        """LOCAL_ONLY with only cloud models should raise ValueError."""
        selector = ModelSelector()
        with pytest.raises(ValueError, match="No local models available"):
            selector.select(
                task_complexity=TaskComplexity.HIGH,
                privacy_mode=PrivacyMode.LOCAL_ONLY,
                available_models=["cloud-best"],
            )


class TestModelSelectorCloudAllowed:
    """Tests for cloud-allowed model selection."""

    def test_cloud_allowed_high_complexity_prefers_cloud(self) -> None:
        """CLOUD_ALLOWED + HIGH → cloud-best."""
        selector = ModelSelector()
        result = selector.select(
            task_complexity=TaskComplexity.HIGH,
            privacy_mode=PrivacyMode.CLOUD_ALLOWED,
        )
        assert result.model == "cloud-best"
        assert result.privacy_compliant is True

    def test_cloud_allowed_medium_complexity_uses_local_powerful(self) -> None:
        """CLOUD_ALLOWED + MEDIUM → local-powerful."""
        selector = ModelSelector()
        result = selector.select(
            task_complexity=TaskComplexity.MEDIUM,
            privacy_mode=PrivacyMode.CLOUD_ALLOWED,
        )
        assert result.model == "local-powerful"

    def test_cloud_allowed_low_complexity_uses_local_fast(self) -> None:
        """CLOUD_ALLOWED + LOW → local-fast for efficiency."""
        selector = ModelSelector()
        result = selector.select(
            task_complexity=TaskComplexity.LOW,
            privacy_mode=PrivacyMode.CLOUD_ALLOWED,
        )
        assert result.model == "local-fast"

    def test_cloud_allowed_falls_back_when_cloud_unavailable(self) -> None:
        """CLOUD_ALLOWED + HIGH with no cloud → local-powerful."""
        selector = ModelSelector()
        result = selector.select(
            task_complexity=TaskComplexity.HIGH,
            privacy_mode=PrivacyMode.CLOUD_ALLOWED,
            available_models=["local-fast", "local-powerful"],
        )
        assert result.model == "local-powerful"


class TestModelSelectorReasoning:
    """Tests that all selections include proper reasoning."""

    def test_all_recommendations_include_reasoning(self) -> None:
        """Every recommendation must have non-empty reasoning."""
        selector = ModelSelector()
        for privacy in [PrivacyMode.LOCAL_ONLY, PrivacyMode.CLOUD_ALLOWED]:
            for complexity in TaskComplexity:
                result = selector.select(complexity, privacy)
                assert result.reasoning, (
                    f"Missing reasoning for {privacy.name} + {complexity.name}"
                )
                assert len(result.reasoning) > 10


class TestPrivacyRecommendation:
    """Tests for automatic privacy mode recommendation."""

    def test_sensitive_keywords_trigger_local_only(self) -> None:
        """Queries with sensitive keywords should recommend LOCAL_ONLY."""
        selector = ModelSelector()
        sensitive_queries = [
            "Analyze this confidential report",
            "Review my private medical records",
            "Process internal company data",
            "Handle patient information",
            "Check salary details",
            "HIPAA compliance check",
        ]

        for query in sensitive_queries:
            mode, reasoning = selector.recommend_privacy_mode(query)
            assert mode == PrivacyMode.LOCAL_ONLY, (
                f"Query '{query}' should trigger LOCAL_ONLY, got {mode.name}"
            )
            assert reasoning  # Should explain why

    def test_general_queries_allow_cloud(self) -> None:
        """Non-sensitive queries should allow cloud processing."""
        selector = ModelSelector()
        general_queries = [
            "What is the capital of France?",
            "Explain quantum computing",
            "Find research papers on machine learning",
            "How does photosynthesis work?",
            "Summarize this article about space exploration",
        ]

        for query in general_queries:
            mode, reasoning = selector.recommend_privacy_mode(query)
            assert mode == PrivacyMode.CLOUD_ALLOWED, (
                f"Query '{query}' should allow cloud, got {mode.name}"
            )

    def test_explicit_sensitive_flag_forces_local(self) -> None:
        """has_sensitive_data=True should always return LOCAL_ONLY."""
        selector = ModelSelector()
        # Even a general query should be local if explicitly flagged
        mode, _ = selector.recommend_privacy_mode(
            "What's the weather?",
            has_sensitive_data=True,
        )
        assert mode == PrivacyMode.LOCAL_ONLY


class TestComplexityEstimation:
    """Tests for task complexity estimation."""

    def test_short_simple_query_is_low(self) -> None:
        """Short queries without complex indicators → LOW."""
        selector = ModelSelector()
        complexity = selector.estimate_complexity("What time is it?")
        assert complexity == TaskComplexity.LOW

    def test_complex_keywords_increase_complexity(self) -> None:
        """Queries with analysis keywords → HIGH."""
        selector = ModelSelector()
        complexity = selector.estimate_complexity(
            "Analyze and compare these two research methodologies in detail"
        )
        assert complexity == TaskComplexity.HIGH

    def test_long_context_increases_complexity(self) -> None:
        """Long context suggests higher complexity."""
        selector = ModelSelector()
        complexity = selector.estimate_complexity("Short query", context_length=3000)
        assert complexity == TaskComplexity.HIGH

    def test_medium_length_is_medium(self) -> None:
        """Medium-length queries without complex keywords → MEDIUM."""
        selector = ModelSelector()
        # Create a query that's over 500 chars but under 2000 and no complex keywords
        medium_query = "Tell me about " + "the history of " * 40
        complexity = selector.estimate_complexity(medium_query)
        assert complexity == TaskComplexity.MEDIUM
