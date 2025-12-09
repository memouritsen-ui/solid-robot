"""Tests for confidence scoring system."""

from research_tool.agent.decisions.confidence import (
    CompositeConfidence,
    SourceQuality,
    calculate_composite_confidence,
    calculate_source_confidence,
    calculate_verification_confidence,
    get_source_quality,
)
from research_tool.models.entities import Fact


class TestSourceQuality:
    """Tests for SourceQuality dataclass."""

    def test_create_source_quality(self) -> None:
        """Test creating a SourceQuality instance."""
        quality = SourceQuality(
            source_name="pubmed",
            credibility=0.9,
            is_peer_reviewed=True,
            is_primary_source=True,
            recency_score=0.8
        )

        assert quality.source_name == "pubmed"
        assert quality.credibility == 0.9
        assert quality.is_peer_reviewed is True

    def test_source_quality_to_dict(self) -> None:
        """Test conversion to dictionary."""
        quality = SourceQuality(
            source_name="wikipedia",
            credibility=0.4,
            is_peer_reviewed=False,
            is_primary_source=False,
            recency_score=0.9
        )

        d = quality.to_dict()
        assert d["source_name"] == "wikipedia"
        assert d["credibility"] == 0.4


class TestGetSourceQuality:
    """Tests for getting source quality scores."""

    def test_pubmed_high_quality(self) -> None:
        """Test that PubMed has high quality score."""
        quality = get_source_quality("pubmed")

        assert quality.credibility >= 0.8
        assert quality.is_peer_reviewed is True

    def test_semantic_scholar_high_quality(self) -> None:
        """Test that Semantic Scholar has high quality."""
        quality = get_source_quality("semantic_scholar")

        assert quality.credibility >= 0.7
        assert quality.is_peer_reviewed is True

    def test_arxiv_medium_quality(self) -> None:
        """Test arXiv quality (preprints, not peer-reviewed)."""
        quality = get_source_quality("arxiv")

        assert quality.credibility >= 0.6
        assert quality.is_peer_reviewed is False  # Preprints

    def test_tavily_general_quality(self) -> None:
        """Test Tavily (general web search) quality."""
        quality = get_source_quality("tavily")

        assert quality.credibility >= 0.4
        assert quality.is_peer_reviewed is False

    def test_unknown_source_default_quality(self) -> None:
        """Test unknown source gets default quality."""
        quality = get_source_quality("unknown_source_xyz")

        assert quality.credibility == 0.3
        assert quality.is_peer_reviewed is False


class TestCalculateSourceConfidence:
    """Tests for source-based confidence calculation."""

    def test_single_high_quality_source(self) -> None:
        """Test confidence with single high-quality source."""
        sources = ["pubmed"]

        confidence = calculate_source_confidence(sources)

        assert confidence > 0.5  # High quality but single source

    def test_multiple_sources_increases_confidence(self) -> None:
        """Test that multiple sources increase confidence."""
        # Use lower-quality sources to avoid hitting 1.0 cap
        single = calculate_source_confidence(["tavily"])
        multiple = calculate_source_confidence(["tavily", "brave"])

        assert multiple > single

    def test_low_quality_sources_lower_confidence(self) -> None:
        """Test that low quality sources give lower confidence."""
        high_quality = calculate_source_confidence(["pubmed", "semantic_scholar"])
        low_quality = calculate_source_confidence(["tavily", "brave"])

        assert high_quality > low_quality

    def test_empty_sources_zero_confidence(self) -> None:
        """Test that empty sources give zero confidence."""
        confidence = calculate_source_confidence([])

        assert confidence == 0.0

    def test_confidence_capped_at_one(self) -> None:
        """Test confidence is capped at 1.0."""
        many_sources = [f"source_{i}" for i in range(20)]

        confidence = calculate_source_confidence(many_sources)

        assert confidence <= 1.0


class TestCalculateVerificationConfidence:
    """Tests for verification-based confidence."""

    def test_verified_fact_high_confidence(self) -> None:
        """Test that verified fact has high confidence."""
        fact = Fact(
            statement="Verified statement",
            sources=["url1", "url2"],
            confidence=0.8,
            verified=True,
            contradictions=[]
        )

        confidence = calculate_verification_confidence(fact)

        assert confidence >= 0.7

    def test_unverified_fact_lower_confidence(self) -> None:
        """Test that unverified fact has lower confidence."""
        verified = Fact(
            statement="Statement",
            sources=["url1"],
            confidence=0.8,
            verified=True,
            contradictions=[]
        )
        unverified = Fact(
            statement="Statement",
            sources=["url1"],
            confidence=0.8,
            verified=False,
            contradictions=[]
        )

        verified_conf = calculate_verification_confidence(verified)
        unverified_conf = calculate_verification_confidence(unverified)

        assert verified_conf > unverified_conf

    def test_contradictions_reduce_confidence(self) -> None:
        """Test that contradictions reduce confidence."""
        no_contradiction = Fact(
            statement="Statement",
            sources=["url1"],
            confidence=0.8,
            verified=True,
            contradictions=[]
        )
        with_contradiction = Fact(
            statement="Statement",
            sources=["url1"],
            confidence=0.8,
            verified=False,
            contradictions=["Conflicting statement"]
        )

        no_contra_conf = calculate_verification_confidence(no_contradiction)
        with_contra_conf = calculate_verification_confidence(with_contradiction)

        assert no_contra_conf > with_contra_conf

    def test_multiple_contradictions_further_reduce(self) -> None:
        """Test multiple contradictions reduce confidence more."""
        one_contradiction = Fact(
            statement="Statement",
            sources=["url1"],
            confidence=0.5,
            verified=False,
            contradictions=["Conflict 1"]
        )
        many_contradictions = Fact(
            statement="Statement",
            sources=["url1"],
            confidence=0.5,
            verified=False,
            contradictions=["Conflict 1", "Conflict 2", "Conflict 3"]
        )

        one_conf = calculate_verification_confidence(one_contradiction)
        many_conf = calculate_verification_confidence(many_contradictions)

        assert one_conf > many_conf


class TestCompositeConfidence:
    """Tests for CompositeConfidence dataclass."""

    def test_create_composite_confidence(self) -> None:
        """Test creating CompositeConfidence."""
        composite = CompositeConfidence(
            source_confidence=0.7,
            verification_confidence=0.8,
            composite_score=0.75,
            explanation="Based on 2 peer-reviewed sources"
        )

        assert composite.composite_score == 0.75
        assert "peer-reviewed" in composite.explanation

    def test_composite_confidence_to_dict(self) -> None:
        """Test conversion to dictionary."""
        composite = CompositeConfidence(
            source_confidence=0.6,
            verification_confidence=0.7,
            composite_score=0.65,
            explanation="Test explanation"
        )

        d = composite.to_dict()
        assert d["composite_score"] == 0.65


class TestCalculateCompositeConfidence:
    """Tests for composite confidence calculation."""

    def test_composite_combines_source_and_verification(self) -> None:
        """Test composite combines both confidence types."""
        fact = Fact(
            statement="Test statement",
            sources=["pubmed", "semantic_scholar"],
            confidence=0.8,
            verified=True,
            contradictions=[]
        )

        composite = calculate_composite_confidence(fact)

        assert composite.source_confidence > 0
        assert composite.verification_confidence > 0
        assert composite.composite_score > 0

    def test_composite_weighted_average(self) -> None:
        """Test composite is weighted average."""
        fact = Fact(
            statement="Test",
            sources=["pubmed"],
            confidence=0.8,
            verified=True,
            contradictions=[]
        )

        composite = calculate_composite_confidence(fact)

        # Composite should be between source and verification
        min_conf = min(composite.source_confidence, composite.verification_confidence)
        max_conf = max(composite.source_confidence, composite.verification_confidence)

        assert min_conf <= composite.composite_score <= max_conf

    def test_composite_includes_explanation(self) -> None:
        """Test composite includes explanation."""
        fact = Fact(
            statement="Test",
            sources=["pubmed"],
            confidence=0.8,
            verified=True,
            contradictions=[]
        )

        composite = calculate_composite_confidence(fact)

        assert len(composite.explanation) > 0

    def test_high_quality_verified_fact_high_composite(self) -> None:
        """Test high quality verified fact gets high composite score."""
        fact = Fact(
            statement="Well-supported statement",
            sources=["pubmed", "semantic_scholar", "arxiv"],
            confidence=0.9,
            verified=True,
            contradictions=[]
        )

        composite = calculate_composite_confidence(fact)

        assert composite.composite_score >= 0.7

    def test_low_quality_contradicted_fact_low_composite(self) -> None:
        """Test low quality contradicted fact gets low composite."""
        fact = Fact(
            statement="Disputed statement",
            sources=["unknown_blog"],
            confidence=0.3,
            verified=False,
            contradictions=["Conflict 1", "Conflict 2"]
        )

        composite = calculate_composite_confidence(fact)

        assert composite.composite_score < 0.4


class TestConfidenceCorrelation:
    """Tests for confidence correlation with source quality."""

    def test_confidence_correlates_with_source_count(self) -> None:
        """Test confidence increases with more sources of same quality."""
        # Use same-quality sources to test source count effect
        sources_1 = ["tavily"]
        sources_2 = ["tavily", "brave"]
        sources_3 = ["tavily", "brave", "exa"]

        conf_1 = calculate_source_confidence(sources_1)
        conf_2 = calculate_source_confidence(sources_2)
        conf_3 = calculate_source_confidence(sources_3)

        # More sources of similar quality = higher confidence
        assert conf_1 < conf_2 < conf_3

    def test_confidence_correlates_with_peer_review(self) -> None:
        """Test peer-reviewed sources give higher confidence."""
        peer_reviewed = ["pubmed", "semantic_scholar"]
        not_peer_reviewed = ["tavily", "brave"]

        peer_conf = calculate_source_confidence(peer_reviewed)
        non_peer_conf = calculate_source_confidence(not_peer_reviewed)

        assert peer_conf > non_peer_conf
