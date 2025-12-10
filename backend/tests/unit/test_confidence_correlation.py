"""Tests for confidence score correlation with accuracy.

Task #234: Test: Confidence scores correlate with accuracy

These tests verify that higher confidence scores correlate with
more accurate/reliable facts.
"""

from research_tool.agent.decisions.confidence import (
    calculate_composite_confidence,
    calculate_source_confidence,
    calculate_verification_confidence,
    get_source_quality,
)
from research_tool.models.entities import Fact


class TestSourceQualityCorrelation:
    """Tests that source quality correlates with confidence."""

    def test_peer_reviewed_sources_higher_confidence(self) -> None:
        """Peer-reviewed sources should give higher confidence."""
        peer_reviewed = ["pubmed", "semantic_scholar", "unpaywall"]
        general_web = ["tavily", "brave", "playwright_crawler"]

        peer_conf = calculate_source_confidence(peer_reviewed)
        general_conf = calculate_source_confidence(general_web)

        assert peer_conf > general_conf, (
            f"Peer-reviewed ({peer_conf:.2f}) should be > general ({general_conf:.2f})"
        )

    def test_more_sources_higher_confidence(self) -> None:
        """More sources of same quality should give higher confidence."""
        # Use same-quality sources to test quantity bonus
        # All tavily = 0.5 credibility each
        one_source = calculate_source_confidence(["tavily"])
        two_sources = calculate_source_confidence(["tavily", "tavily"])
        three_sources = calculate_source_confidence(["tavily", "tavily", "tavily"])

        # More sources should add bonus (logarithmic)
        assert two_sources > one_source, (
            f"2 sources ({two_sources:.2f}) > 1 source ({one_source:.2f})"
        )
        assert three_sources > two_sources, (
            f"3 sources ({three_sources:.2f}) > 2 sources ({two_sources:.2f})"
        )

    def test_academic_sources_higher_than_web(self) -> None:
        """Academic sources should have higher credibility."""
        academic_quality = get_source_quality("pubmed")
        web_quality = get_source_quality("brave")

        assert academic_quality.credibility > web_quality.credibility

    def test_unknown_source_low_confidence(self) -> None:
        """Unknown sources should have low base confidence."""
        unknown = get_source_quality("random_unknown_site.com")

        assert unknown.credibility < 0.5
        assert unknown.is_peer_reviewed is False


class TestVerificationCorrelation:
    """Tests that verification status correlates with confidence."""

    def test_verified_fact_higher_confidence(self) -> None:
        """Verified facts should have higher confidence."""
        verified = Fact(
            statement="Test statement",
            sources=["pubmed"],
            confidence=0.7,
            verified=True,
        )
        unverified = Fact(
            statement="Test statement",
            sources=["pubmed"],
            confidence=0.7,
            verified=False,
        )

        verified_conf = calculate_verification_confidence(verified)
        unverified_conf = calculate_verification_confidence(unverified)

        assert verified_conf > unverified_conf, (
            f"Verified ({verified_conf:.2f}) > unverified ({unverified_conf:.2f})"
        )

    def test_contradictions_reduce_confidence(self) -> None:
        """Facts with contradictions should have lower confidence."""
        no_contradictions = Fact(
            statement="Test statement",
            sources=["pubmed"],
            confidence=0.8,
            verified=True,
            contradictions=[],
        )
        with_contradictions = Fact(
            statement="Test statement",
            sources=["pubmed"],
            confidence=0.8,
            verified=True,
            contradictions=["Conflicting source says otherwise"],
        )

        clean_conf = calculate_verification_confidence(no_contradictions)
        contradicted_conf = calculate_verification_confidence(with_contradictions)

        assert clean_conf > contradicted_conf, (
            f"Clean ({clean_conf:.2f}) > contradicted ({contradicted_conf:.2f})"
        )

    def test_multiple_contradictions_lower_confidence(self) -> None:
        """More contradictions = lower confidence."""
        one_contradiction = Fact(
            statement="Test",
            sources=["pubmed"],
            confidence=0.8,
            verified=False,
            contradictions=["Contradiction 1"],
        )
        three_contradictions = Fact(
            statement="Test",
            sources=["pubmed"],
            confidence=0.8,
            verified=False,
            contradictions=["Contradiction 1", "Contradiction 2", "Contradiction 3"],
        )

        one_conf = calculate_verification_confidence(one_contradiction)
        three_conf = calculate_verification_confidence(three_contradictions)

        assert one_conf > three_conf, (
            f"1 contradiction ({one_conf:.2f}) > 3 ({three_conf:.2f})"
        )


class TestCompositeConfidenceCorrelation:
    """Tests that composite confidence correctly combines factors."""

    def test_high_quality_verified_fact_high_confidence(self) -> None:
        """High-quality, verified fact should have high composite confidence."""
        high_quality = Fact(
            statement="Well-sourced verified fact",
            sources=["pubmed", "semantic_scholar", "unpaywall"],
            confidence=0.9,
            verified=True,
            contradictions=[],
        )

        composite = calculate_composite_confidence(high_quality)

        assert composite.composite_score > 0.7, (
            f"High-quality verified fact should be >0.7: {composite.composite_score:.2f}"
        )

    def test_low_quality_unverified_fact_low_confidence(self) -> None:
        """Low-quality, unverified fact should have low composite confidence."""
        low_quality = Fact(
            statement="Poorly-sourced unverified fact",
            sources=["random_blog.com"],
            confidence=0.3,
            verified=False,
            contradictions=["Another source disagrees"],
        )

        composite = calculate_composite_confidence(low_quality)

        assert composite.composite_score < 0.5, (
            f"Low-quality fact should be <0.5: {composite.composite_score:.2f}"
        )

    def test_composite_reflects_both_source_and_verification(self) -> None:
        """Composite score should reflect both components."""
        fact = Fact(
            statement="Test fact",
            sources=["pubmed", "arxiv"],
            confidence=0.75,
            verified=True,
            contradictions=[],
        )

        composite = calculate_composite_confidence(fact)

        # Composite should be between source and verification confidence
        assert composite.source_confidence > 0
        assert composite.verification_confidence > 0
        # Composite is weighted average, should be reasonable
        assert 0.3 < composite.composite_score < 1.0

    def test_composite_explanation_informative(self) -> None:
        """Composite should include informative explanation."""
        fact = Fact(
            statement="Test fact",
            sources=["pubmed", "semantic_scholar"],
            confidence=0.8,
            verified=True,
            contradictions=[],
        )

        composite = calculate_composite_confidence(fact)

        assert len(composite.explanation) > 10
        assert "source" in composite.explanation.lower() or "2" in composite.explanation


class TestConfidenceAccuracyCorrelation:
    """Tests that confidence correlates with fact accuracy patterns."""

    def test_accurate_fact_pattern_high_confidence(self) -> None:
        """Pattern of accurate facts should have high confidence."""
        # Accurate fact pattern: multiple peer-reviewed, verified, no contradictions
        accurate_patterns = [
            Fact(
                statement="Earth orbits the Sun",
                sources=["pubmed", "semantic_scholar", "arxiv"],
                confidence=0.95,
                verified=True,
                contradictions=[],
            ),
            Fact(
                statement="Water boils at 100C at sea level",
                sources=["pubmed", "unpaywall"],
                confidence=0.9,
                verified=True,
                contradictions=[],
            ),
        ]

        for fact in accurate_patterns:
            composite = calculate_composite_confidence(fact)
            assert composite.composite_score > 0.6, (
                f"Accurate pattern should have high confidence: {composite}"
            )

    def test_dubious_fact_pattern_low_confidence(self) -> None:
        """Pattern of dubious facts should have low confidence."""
        # Dubious pattern: single web source, unverified, contradictions
        dubious_patterns = [
            Fact(
                statement="Unverified claim from blog",
                sources=["random_blog.com"],
                confidence=0.3,
                verified=False,
                contradictions=["Official sources say otherwise"],
            ),
            Fact(
                statement="Contradicted claim",
                sources=["tavily"],
                confidence=0.4,
                verified=False,
                contradictions=["Source A disagrees", "Source B disagrees"],
            ),
        ]

        for fact in dubious_patterns:
            composite = calculate_composite_confidence(fact)
            assert composite.composite_score < 0.5, (
                f"Dubious pattern should have low confidence: {composite}"
            )

    def test_confidence_ordering_matches_reliability(self) -> None:
        """Confidence ordering should match expected reliability."""
        # Create facts with known reliability ordering
        highly_reliable = Fact(
            statement="Highly reliable",
            sources=["pubmed", "semantic_scholar", "unpaywall"],
            confidence=0.9,
            verified=True,
            contradictions=[],
        )
        moderately_reliable = Fact(
            statement="Moderately reliable",
            sources=["arxiv", "tavily"],
            confidence=0.6,
            verified=True,
            contradictions=[],
        )
        low_reliability = Fact(
            statement="Low reliability",
            sources=["brave"],
            confidence=0.4,
            verified=False,
            contradictions=["Conflicting info"],
        )

        high_conf = calculate_composite_confidence(highly_reliable).composite_score
        med_conf = calculate_composite_confidence(moderately_reliable).composite_score
        low_conf = calculate_composite_confidence(low_reliability).composite_score

        assert high_conf > med_conf > low_conf, (
            f"Ordering wrong: high={high_conf:.2f}, med={med_conf:.2f}, low={low_conf:.2f}"
        )
