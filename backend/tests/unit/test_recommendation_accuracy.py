"""Tests for recommendation system accuracy.

Task #231: Test: Recommendations accurate for test cases.

These tests verify that:
1. Privacy mode recommendations match expected for various query types
2. Model selection matches expected based on complexity + privacy
3. Explanations are clear and accurate
"""

import pytest

from research_tool.services.llm.selector import (
    ModelSelector,
    PrivacyMode,
    TaskComplexity,
)


class TestPrivacyModeRecommendationAccuracy:
    """Verify privacy mode recommendations are accurate for test cases."""

    @pytest.fixture
    def selector(self) -> ModelSelector:
        """Create ModelSelector instance."""
        return ModelSelector()

    # === MEDICAL QUERIES - Should be LOCAL_ONLY ===

    @pytest.mark.parametrize(
        "query",
        [
            "Review patient medical history",
            "Analyze lab results for diagnosis",
            "Check HIPAA compliance requirements",
            "Process healthcare treatment data",
            "Look up patient symptoms",
        ],
    )
    def test_medical_queries_recommend_local_only(
        self, selector: ModelSelector, query: str
    ) -> None:
        """Medical queries should recommend LOCAL_ONLY."""
        mode, reasoning = selector.recommend_privacy_mode(query)

        assert mode == PrivacyMode.LOCAL_ONLY, (
            f"Medical query '{query}' should recommend LOCAL_ONLY, "
            f"got {mode.value}. Reason: {reasoning}"
        )

    # === FINANCIAL QUERIES - Should be LOCAL_ONLY ===

    @pytest.mark.parametrize(
        "query",
        [
            "Check my salary information",
            "Analyze financial statements",
            "Review bank account transactions",
            "Process credit card data",
            "Calculate investment returns",
        ],
    )
    def test_financial_queries_recommend_local_only(
        self, selector: ModelSelector, query: str
    ) -> None:
        """Financial queries should recommend LOCAL_ONLY."""
        mode, reasoning = selector.recommend_privacy_mode(query)

        assert mode == PrivacyMode.LOCAL_ONLY, (
            f"Financial query '{query}' should recommend LOCAL_ONLY, "
            f"got {mode.value}. Reason: {reasoning}"
        )

    # === PII QUERIES - Should be LOCAL_ONLY ===

    @pytest.mark.parametrize(
        "query",
        [
            "Store user SSN for verification",
            "Process personal identification",
            "Update password credentials",
            "Handle GDPR personal data",
            "Verify user identity information",
        ],
    )
    def test_pii_queries_recommend_local_only(
        self, selector: ModelSelector, query: str
    ) -> None:
        """PII queries should recommend LOCAL_ONLY."""
        mode, reasoning = selector.recommend_privacy_mode(query)

        assert mode == PrivacyMode.LOCAL_ONLY, (
            f"PII query '{query}' should recommend LOCAL_ONLY, "
            f"got {mode.value}. Reason: {reasoning}"
        )

    # === CORPORATE CONFIDENTIAL - Should be LOCAL_ONLY ===

    @pytest.mark.parametrize(
        "query",
        [
            "Analyze confidential merger documents",
            "Review internal strategy plans",
            "Process proprietary algorithm",
            "Handle NDA protected information",
            "Analyze trade secret formulation",
        ],
    )
    def test_corporate_queries_recommend_local_only(
        self, selector: ModelSelector, query: str
    ) -> None:
        """Corporate confidential queries should recommend LOCAL_ONLY."""
        mode, reasoning = selector.recommend_privacy_mode(query)

        assert mode == PrivacyMode.LOCAL_ONLY, (
            f"Corporate query '{query}' should recommend LOCAL_ONLY, "
            f"got {mode.value}. Reason: {reasoning}"
        )

    # === GENERAL QUERIES - Should be CLOUD_ALLOWED ===

    @pytest.mark.parametrize(
        "query",
        [
            "What is the capital of France?",
            "Explain quantum computing basics",
            "History of the Roman Empire",
            "Best restaurants in Copenhagen",
            "How does photosynthesis work?",
            "Latest developments in AI",
            "Weather forecast for tomorrow",
            "Recipe for chocolate cake",
            "How to learn Python programming",
            "Summarize the latest news",
        ],
    )
    def test_general_queries_allow_cloud(
        self, selector: ModelSelector, query: str
    ) -> None:
        """General knowledge queries should allow cloud processing."""
        mode, reasoning = selector.recommend_privacy_mode(query)

        assert mode == PrivacyMode.CLOUD_ALLOWED, (
            f"General query '{query}' should allow CLOUD, "
            f"got {mode.value}. Reason: {reasoning}"
        )


class TestModelSelectionAccuracy:
    """Verify model selection matches expected for complexity + privacy."""

    @pytest.fixture
    def selector(self) -> ModelSelector:
        """Create ModelSelector instance."""
        return ModelSelector()

    # === LOCAL_ONLY MODE ===

    def test_local_only_high_selects_local_powerful(
        self, selector: ModelSelector
    ) -> None:
        """LOCAL_ONLY + HIGH complexity → local-powerful."""
        result = selector.select(TaskComplexity.HIGH, PrivacyMode.LOCAL_ONLY)

        assert result.model == "local-powerful"
        assert result.privacy_compliant is True
        assert "cloud" not in result.model

    def test_local_only_medium_selects_local_fast(
        self, selector: ModelSelector
    ) -> None:
        """LOCAL_ONLY + MEDIUM complexity → local-fast."""
        result = selector.select(TaskComplexity.MEDIUM, PrivacyMode.LOCAL_ONLY)

        assert result.model == "local-fast"
        assert result.privacy_compliant is True

    def test_local_only_low_selects_local_fast(
        self, selector: ModelSelector
    ) -> None:
        """LOCAL_ONLY + LOW complexity → local-fast."""
        result = selector.select(TaskComplexity.LOW, PrivacyMode.LOCAL_ONLY)

        assert result.model == "local-fast"
        assert result.privacy_compliant is True

    # === CLOUD_ALLOWED MODE ===

    def test_cloud_allowed_high_selects_cloud_best(
        self, selector: ModelSelector
    ) -> None:
        """CLOUD_ALLOWED + HIGH complexity → cloud-best."""
        result = selector.select(TaskComplexity.HIGH, PrivacyMode.CLOUD_ALLOWED)

        assert result.model == "cloud-best"
        assert result.privacy_compliant is True

    def test_cloud_allowed_medium_selects_local_powerful(
        self, selector: ModelSelector
    ) -> None:
        """CLOUD_ALLOWED + MEDIUM complexity → local-powerful."""
        result = selector.select(TaskComplexity.MEDIUM, PrivacyMode.CLOUD_ALLOWED)

        assert result.model == "local-powerful"
        assert result.privacy_compliant is True

    def test_cloud_allowed_low_selects_local_fast(
        self, selector: ModelSelector
    ) -> None:
        """CLOUD_ALLOWED + LOW complexity → local-fast."""
        result = selector.select(TaskComplexity.LOW, PrivacyMode.CLOUD_ALLOWED)

        assert result.model == "local-fast"
        assert result.privacy_compliant is True


class TestComplexityEstimationAccuracy:
    """Verify complexity estimation is accurate for test cases."""

    @pytest.fixture
    def selector(self) -> ModelSelector:
        """Create ModelSelector instance."""
        return ModelSelector()

    @pytest.mark.parametrize(
        "query,expected",
        [
            ("What time is it?", TaskComplexity.LOW),
            ("Hello", TaskComplexity.LOW),
            ("Define X", TaskComplexity.LOW),
            ("Analyze and compare these research methodologies", TaskComplexity.HIGH),
            ("Provide a comprehensive evaluation", TaskComplexity.HIGH),
            ("Synthesize information from multiple sources", TaskComplexity.HIGH),
            ("Perform detailed in-depth analysis", TaskComplexity.HIGH),
        ],
    )
    def test_complexity_estimation_accuracy(
        self, selector: ModelSelector, query: str, expected: TaskComplexity
    ) -> None:
        """Complexity estimation should match expected for test queries."""
        result = selector.estimate_complexity(query)

        assert result == expected, (
            f"Query '{query}' should be {expected.name}, got {result.name}"
        )

    def test_long_context_increases_complexity(
        self, selector: ModelSelector
    ) -> None:
        """Long context should increase complexity estimation."""
        # Simple query with long context → HIGH complexity
        result = selector.estimate_complexity("Short query", context_length=3000)

        assert result == TaskComplexity.HIGH


class TestExplanationQuality:
    """Verify explanations are clear and informative."""

    @pytest.fixture
    def selector(self) -> ModelSelector:
        """Create ModelSelector instance."""
        return ModelSelector()

    def test_privacy_explanation_mentions_detected_content(
        self, selector: ModelSelector
    ) -> None:
        """Privacy explanation should mention what was detected."""
        mode, reasoning = selector.recommend_privacy_mode("patient medical records")

        assert mode == PrivacyMode.LOCAL_ONLY
        # Should explain what triggered the recommendation
        assert any(
            term in reasoning.lower()
            for term in ["medical", "sensitive", "patient", "semantic", "detected"]
        ), f"Explanation should mention detected content. Got: {reasoning}"

    def test_model_selection_explanation_mentions_factors(
        self, selector: ModelSelector
    ) -> None:
        """Model selection explanation should mention relevant factors."""
        result = selector.select(TaskComplexity.HIGH, PrivacyMode.LOCAL_ONLY)

        # Should explain why this model was chosen
        assert "local" in result.reasoning.lower() or "privacy" in result.reasoning.lower()
        assert len(result.reasoning) > 20  # Should be meaningful, not just a word

    def test_cloud_allowed_explanation_is_clear(
        self, selector: ModelSelector
    ) -> None:
        """Cloud allowed explanation should be clear and informative."""
        mode, reasoning = selector.recommend_privacy_mode("What is Python?")

        assert mode == PrivacyMode.CLOUD_ALLOWED
        assert "cloud" in reasoning.lower() or "no sensitive" in reasoning.lower()
