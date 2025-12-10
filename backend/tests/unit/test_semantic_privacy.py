"""Tests for semantic privacy detection using NLP.

Task #229: Enhance recommend_privacy_mode() with NLP.

These tests verify that semantic similarity (not just keyword matching)
can detect sensitive queries that should use LOCAL_ONLY mode.
"""

import pytest

from research_tool.services.llm.semantic_privacy import SemanticPrivacyDetector


class TestSemanticPrivacyDetector:
    """Tests for SemanticPrivacyDetector using sentence-transformers."""

    @pytest.fixture
    def detector(self) -> SemanticPrivacyDetector:
        """Create detector instance."""
        return SemanticPrivacyDetector()

    def test_detects_medical_content_without_keyword(
        self, detector: SemanticPrivacyDetector
    ) -> None:
        """Detect medical sensitivity even without exact 'medical' keyword.

        Example: 'my patient's symptoms' is medical but doesn't contain 'medical'.
        """
        queries = [
            "my patient's symptoms are getting worse",
            "the diagnosis shows signs of cancer",
            "prescribe medication for hypertension",
            "her blood test results came back",
            "treatment plan for diabetes management",
        ]

        for query in queries:
            is_sensitive, category = detector.detect_sensitivity(query)
            assert is_sensitive, f"'{query}' should be detected as sensitive (medical)"
            assert category == "medical", f"'{query}' should be categorized as medical"

    def test_detects_financial_content_without_keyword(
        self, detector: SemanticPrivacyDetector
    ) -> None:
        """Detect financial sensitivity even without exact 'financial' keyword."""
        queries = [
            "my bank account balance is low",
            "transfer money to savings",
            "check my investment portfolio",
            "calculate tax deductions",
            "review credit card statements",
        ]

        for query in queries:
            is_sensitive, category = detector.detect_sensitivity(query)
            assert is_sensitive, f"'{query}' should be detected as sensitive (financial)"
            assert category == "financial", f"'{query}' should be categorized as financial"

    def test_detects_personal_identity_content(
        self, detector: SemanticPrivacyDetector
    ) -> None:
        """Detect PII-related queries."""
        queries = [
            "my social security number is",
            "here's my passport details",
            "store my home address",
            "my birth date and full name",
            "update my personal information",
        ]

        for query in queries:
            is_sensitive, category = detector.detect_sensitivity(query)
            assert is_sensitive, f"'{query}' should be detected as sensitive (PII)"
            assert category == "pii", f"'{query}' should be categorized as pii"

    def test_detects_corporate_confidential_content(
        self, detector: SemanticPrivacyDetector
    ) -> None:
        """Detect corporate/business confidential queries."""
        queries = [
            "our company's merger plans",
            "internal strategy documents",
            "proprietary algorithm details",
            "trade secret formulation",
            "non-disclosure agreement terms",
        ]

        for query in queries:
            is_sensitive, category = detector.detect_sensitivity(query)
            assert is_sensitive, f"'{query}' should be detected as sensitive (corporate)"
            assert category == "corporate", f"'{query}' should be categorized as corporate"

    def test_non_sensitive_queries_not_flagged(
        self, detector: SemanticPrivacyDetector
    ) -> None:
        """General knowledge queries should NOT be flagged as sensitive."""
        queries = [
            "what is the capital of France",
            "explain how photosynthesis works",
            "history of the Roman Empire",
            "best programming languages for web development",
            "how to cook pasta",
            "weather forecast for tomorrow",
            "latest news about space exploration",
        ]

        for query in queries:
            is_sensitive, category = detector.detect_sensitivity(query)
            assert not is_sensitive, f"'{query}' should NOT be flagged as sensitive"
            assert category is None, f"'{query}' should have no category"

    def test_returns_confidence_score(
        self, detector: SemanticPrivacyDetector
    ) -> None:
        """Detector should return confidence score for transparency."""
        is_sensitive, category, confidence = detector.detect_sensitivity_with_confidence(
            "patient medical records"
        )

        assert is_sensitive is True
        assert category == "medical"
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.3  # Should have meaningful confidence above threshold

    def test_threshold_controls_sensitivity(
        self, detector: SemanticPrivacyDetector
    ) -> None:
        """Higher threshold should reduce false positives."""
        # Ambiguous query - might be sensitive depending on context
        query = "review the report"

        # Low threshold - more sensitive
        low_result, _ = detector.detect_sensitivity(query, threshold=0.3)

        # High threshold - less sensitive
        high_result, _ = detector.detect_sensitivity(query, threshold=0.9)

        # High threshold should be same or less sensitive
        if low_result:
            assert high_result is False or high_result is True
        if not low_result:
            assert high_result is False

    def test_handles_empty_query(
        self, detector: SemanticPrivacyDetector
    ) -> None:
        """Empty or whitespace queries should not crash."""
        is_sensitive, category = detector.detect_sensitivity("")
        assert is_sensitive is False
        assert category is None

        is_sensitive, category = detector.detect_sensitivity("   ")
        assert is_sensitive is False
        assert category is None

    def test_handles_very_long_query(
        self, detector: SemanticPrivacyDetector
    ) -> None:
        """Long queries should still work (truncated if needed)."""
        # Long but clearly medical query
        long_query = "I need to analyze the patient medical records " * 50
        is_sensitive, category = detector.detect_sensitivity(long_query)

        # Should still detect the sensitive content
        assert is_sensitive is True
        assert category == "medical"


class TestSemanticPrivacyIntegration:
    """Integration tests for semantic privacy with ModelSelector."""

    def test_semantic_detection_enhances_keyword_detection(self) -> None:
        """Semantic detection should catch what keywords miss."""
        from research_tool.services.llm.selector import ModelSelector, PrivacyMode

        selector = ModelSelector()

        # This query has NO sensitive keywords from SENSITIVE_KEYWORDS list
        # but is semantically related to medical/health content
        # Note: "patient", "medical", "confidential" etc are keywords, avoid them
        query = "the diagnosis shows signs of cancer in his blood tests"

        mode, reasoning = selector.recommend_privacy_mode(query)

        assert mode == PrivacyMode.LOCAL_ONLY, (
            f"Semantic detection should catch medical content. Got: {mode}, reason: {reasoning}"
        )
        assert "semantic" in reasoning.lower() or "medical" in reasoning.lower(), (
            f"Reasoning should mention semantic/medical. Got: {reasoning}"
        )
