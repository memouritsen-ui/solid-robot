"""Tests for domain detection from META guide Section 7.2."""

import pytest

from research_tool.agent.decisions.domain_detector import (
    DetectedDomain,
    detect_domain,
    detect_domain_with_llm,
    get_domain_keywords,
)
from research_tool.models.domain import DomainConfiguration


class TestDetectedDomain:
    """Tests for DetectedDomain dataclass."""

    def test_create_detected_domain(self) -> None:
        """Test creating a DetectedDomain instance."""
        result = DetectedDomain(
            domain="medical",
            confidence=0.85,
            matched_keywords=["patient", "treatment"],
            detection_method="keyword"
        )

        assert result.domain == "medical"
        assert result.confidence == 0.85
        assert result.matched_keywords == ["patient", "treatment"]
        assert result.detection_method == "keyword"

    def test_detected_domain_to_dict(self) -> None:
        """Test conversion to dictionary."""
        result = DetectedDomain(
            domain="academic",
            confidence=0.75,
            matched_keywords=["research", "study"],
            detection_method="keyword"
        )

        d = result.to_dict()
        assert d["domain"] == "academic"
        assert d["confidence"] == 0.75
        assert d["matched_keywords"] == ["research", "study"]
        assert d["detection_method"] == "keyword"


class TestDetectDomain:
    """Tests for keyword-based domain detection."""

    def test_detect_medical_domain(self) -> None:
        """Test detection of medical domain."""
        query = "What are the latest treatments for type 2 diabetes in patients?"

        result = detect_domain(query)

        assert result.domain == "medical"
        assert result.confidence > 0  # Keywords matched
        assert "treatment" in result.matched_keywords or "patient" in result.matched_keywords
        assert result.detection_method == "keyword"

    def test_detect_competitive_intelligence_domain(self) -> None:
        """Test detection of competitive intelligence domain."""
        query = "What is the market share and revenue of our main competitor?"

        result = detect_domain(query)

        assert result.domain == "competitive_intelligence"
        assert result.confidence > 0  # Keywords matched
        assert any(kw in result.matched_keywords for kw in ["market", "competitor", "revenue"])

    def test_detect_academic_domain(self) -> None:
        """Test detection of academic domain."""
        query = "Find peer-reviewed research papers on methodology in citation analysis"

        result = detect_domain(query)

        assert result.domain == "academic"
        assert result.confidence > 0  # Keywords matched
        expected_kw = ["research", "paper", "peer-reviewed", "methodology", "citation"]
        assert any(kw in result.matched_keywords for kw in expected_kw)

    def test_detect_regulatory_domain(self) -> None:
        """Test detection of regulatory domain."""
        query = "What are the FDA compliance requirements for medical device regulations?"

        result = detect_domain(query)

        assert result.domain == "regulatory"
        assert result.confidence > 0  # Keywords matched
        expected_kw = ["fda", "compliance", "regulation", "requirement"]
        assert any(kw in result.matched_keywords for kw in expected_kw)

    def test_unknown_domain_returns_general(self) -> None:
        """Test that unknown domains return general."""
        query = "What is the weather like today?"

        result = detect_domain(query)

        assert result.domain == "general"
        assert result.confidence < 0.5
        assert result.matched_keywords == []

    def test_case_insensitive_matching(self) -> None:
        """Test that keyword matching is case-insensitive."""
        query = "PATIENT TREATMENT for DISEASE"

        result = detect_domain(query)

        assert result.domain == "medical"
        assert result.confidence > 0  # Keywords matched

    def test_multiple_domain_keywords_increases_confidence(self) -> None:
        """Test that more keyword matches increase confidence."""
        # Single keyword
        single_kw_query = "patient care"
        single_result = detect_domain(single_kw_query)

        # Multiple keywords
        multi_kw_query = "patient treatment for disease diagnosis and therapy"
        multi_result = detect_domain(multi_kw_query)

        assert multi_result.confidence > single_result.confidence

    def test_tie_breaker_prefers_medical_over_general(self) -> None:
        """Test that medical domain is preferred over general in ties."""
        # Query with both medical and general terms
        query = "clinical research study on treatment"

        result = detect_domain(query)

        # Should prefer medical due to "clinical" and "treatment"
        assert result.domain in ("medical", "academic")


class TestGetDomainKeywords:
    """Tests for getting domain keywords."""

    def test_get_medical_keywords(self) -> None:
        """Test getting medical domain keywords."""
        keywords = get_domain_keywords("medical")

        assert "patient" in keywords
        assert "treatment" in keywords
        assert "clinical" in keywords

    def test_get_competitive_intelligence_keywords(self) -> None:
        """Test getting competitive intelligence keywords."""
        keywords = get_domain_keywords("competitive_intelligence")

        assert "market" in keywords
        assert "competitor" in keywords
        assert "revenue" in keywords

    def test_get_academic_keywords(self) -> None:
        """Test getting academic domain keywords."""
        keywords = get_domain_keywords("academic")

        assert "research" in keywords
        assert "paper" in keywords
        assert "journal" in keywords

    def test_get_regulatory_keywords(self) -> None:
        """Test getting regulatory domain keywords."""
        keywords = get_domain_keywords("regulatory")

        assert "regulation" in keywords
        assert "compliance" in keywords
        assert "FDA" in keywords

    def test_unknown_domain_returns_empty(self) -> None:
        """Test that unknown domain returns empty list."""
        keywords = get_domain_keywords("unknown_domain_xyz")

        assert keywords == []


class TestDetectDomainWithLLM:
    """Tests for LLM-based domain detection (fallback)."""

    @pytest.mark.asyncio
    async def test_llm_detection_returns_detected_domain(self) -> None:
        """Test that LLM detection returns DetectedDomain."""
        query = "complex ambiguous query without clear keywords"

        result = await detect_domain_with_llm(query)

        assert isinstance(result, DetectedDomain)
        assert result.detection_method == "llm"

    @pytest.mark.asyncio
    async def test_llm_detection_for_novel_domain(self) -> None:
        """Test LLM detection for queries without keyword matches."""
        query = "How do neural networks learn to recognize images?"

        result = await detect_domain_with_llm(query)

        assert isinstance(result, DetectedDomain)
        # Should detect something related to technology/academic
        assert result.domain in ("academic", "technology", "general")

    @pytest.mark.asyncio
    async def test_llm_detection_confidence_range(self) -> None:
        """Test that LLM detection returns valid confidence range."""
        query = "any query for testing"

        result = await detect_domain_with_llm(query)

        assert 0.0 <= result.confidence <= 1.0


class TestDomainDetectorIntegration:
    """Integration tests for domain detection with DomainConfiguration."""

    def test_detected_domain_matches_config_domains(self) -> None:
        """Test that detected domains match available DomainConfiguration domains."""
        valid_domains = {"medical", "competitive_intelligence", "academic", "regulatory", "general"}

        test_queries = [
            "patient treatment options",
            "competitor market analysis",
            "research paper methodology",
            "FDA compliance requirements",
            "random unrelated query"
        ]

        for query in test_queries:
            result = detect_domain(query)
            msg = f"Invalid domain {result.domain} for query: {query}"
            assert result.domain in valid_domains, msg

    def test_detected_domain_can_load_config(self) -> None:
        """Test that detected domain can load corresponding DomainConfiguration."""
        query = "clinical treatment for patients with disease"

        result = detect_domain(query)

        # Should be able to get config for detected domain
        if result.domain == "medical":
            config = DomainConfiguration.for_medical()
        elif result.domain == "competitive_intelligence":
            config = DomainConfiguration.for_competitive_intelligence()
        elif result.domain == "academic":
            config = DomainConfiguration.for_academic()
        elif result.domain == "regulatory":
            config = DomainConfiguration.for_regulatory()
        else:
            config = DomainConfiguration.default()

        is_general = result.domain == "general" and config.domain == "general"
        assert config.domain == result.domain or is_general
