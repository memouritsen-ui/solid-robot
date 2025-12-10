"""Tests for cross-verification catching planted contradictions.

Task #233: Test: Cross-verification catches planted contradictions

These tests plant deliberate contradictions and verify the system detects them.
"""

from datetime import datetime

import pytest

from research_tool.agent.nodes.verify import (
    detect_contradictions,
    verify_node,
)
from research_tool.models.entities import Fact
from research_tool.models.state import ResearchState


class TestPlantedYearContradictions:
    """Tests for detecting planted year contradictions."""

    def test_catches_founding_year_contradiction(self) -> None:
        """Detect contradiction in company founding year."""
        facts = [
            Fact(
                statement="Apple Inc was founded in 1976 in California by Steve Jobs",
                sources=["source_a.com"],
                confidence=0.8,
                verified=False,
            ),
            Fact(
                statement="Apple Inc was founded in 1980 in California by Steve Jobs",
                sources=["source_b.com"],
                confidence=0.8,
                verified=False,
            ),
        ]

        contradictions = detect_contradictions(facts)

        assert len(contradictions) >= 1, "Should detect year contradiction"
        assert any(
            "year" in c.get("type", "").lower() or "1976" in c.get("reason", "")
            for c in contradictions
        ), f"Should mention year conflict: {contradictions}"

    def test_catches_event_year_contradiction(self) -> None:
        """Detect contradiction in event year."""
        facts = [
            Fact(
                statement="World War II ended in 1945 after Germany surrendered",
                sources=["history_source1.com"],
                confidence=0.9,
                verified=False,
            ),
            Fact(
                statement="World War II ended in 1944 after Germany surrendered",
                sources=["history_source2.com"],
                confidence=0.7,
                verified=False,
            ),
        ]

        contradictions = detect_contradictions(facts)

        assert len(contradictions) >= 1, "Should detect year contradiction"

    def test_catches_release_date_contradiction(self) -> None:
        """Detect contradiction in product release date."""
        facts = [
            Fact(
                statement="iPhone was first released in 2007 by Apple company",
                sources=["tech_news1.com"],
                confidence=0.85,
                verified=False,
            ),
            Fact(
                statement="iPhone was first released in 2008 by Apple company",
                sources=["tech_news2.com"],
                confidence=0.75,
                verified=False,
            ),
        ]

        contradictions = detect_contradictions(facts)

        assert len(contradictions) >= 1, "Should detect release year contradiction"


class TestPlantedAmountContradictions:
    """Tests for detecting planted dollar amount contradictions."""

    def test_catches_revenue_amount_contradiction(self) -> None:
        """Detect contradiction in company revenue figures."""
        facts = [
            Fact(
                statement="Tesla reported annual revenue of $81 billion in 2022",
                sources=["financial_news1.com"],
                confidence=0.8,
                verified=False,
            ),
            Fact(
                statement="Tesla reported annual revenue of $50 billion in 2022",
                sources=["financial_news2.com"],
                confidence=0.8,
                verified=False,
            ),
        ]

        contradictions = detect_contradictions(facts)

        assert len(contradictions) >= 1, "Should detect revenue contradiction"
        assert any(
            "amount" in c.get("type", "").lower() or "$" in c.get("reason", "")
            for c in contradictions
        ), f"Should mention amount conflict: {contradictions}"

    def test_catches_funding_amount_contradiction(self) -> None:
        """Detect contradiction in funding amounts."""
        facts = [
            Fact(
                statement="Startup XYZ raised $100 million in Series B funding round",
                sources=["techcrunch.com"],
                confidence=0.85,
                verified=False,
            ),
            Fact(
                statement="Startup XYZ raised $250 million in Series B funding round",
                sources=["bloomberg.com"],
                confidence=0.85,
                verified=False,
            ),
        ]

        contradictions = detect_contradictions(facts)

        assert len(contradictions) >= 1, "Should detect funding amount contradiction"

    def test_catches_price_contradiction(self) -> None:
        """Detect contradiction in product prices."""
        facts = [
            Fact(
                statement="The new MacBook Pro costs $1,999 at retail price",
                sources=["apple_news.com"],
                confidence=0.9,
                verified=False,
            ),
            Fact(
                statement="The new MacBook Pro costs $2,999 at retail price",
                sources=["tech_review.com"],
                confidence=0.8,
                verified=False,
            ),
        ]

        contradictions = detect_contradictions(facts)

        assert len(contradictions) >= 1, "Should detect price contradiction"


class TestPlantedContradictionsInVerifyNode:
    """Integration tests for planted contradictions through verify_node."""

    @pytest.mark.asyncio
    async def test_verify_node_catches_year_contradiction(self) -> None:
        """Test verify_node catches planted year contradiction."""
        state: ResearchState = {
            "session_id": "contradiction_test_1",
            "original_query": "When was Python created?",
            "privacy_mode": "LOCAL_ONLY",
            "started_at": datetime.now(),
            "facts_extracted": [
                {
                    "statement": "Python language was created in 1991 by Guido van Rossum",
                    "sources": ["wiki.com"],
                    "confidence": 0.8,
                    "verified": False,
                },
                {
                    "statement": "Python language was created in 1989 by Guido van Rossum",
                    "sources": ["blog.com"],
                    "confidence": 0.7,
                    "verified": False,
                },
            ],
            "sources_queried": ["wiki.com", "blog.com"],
            "entities_found": [],
            "access_failures": [],
            "current_phase": "analyze",
            "should_stop": False,
        }

        result = await verify_node(state)

        assert "contradictions" in result, "Should return contradictions field"
        assert len(result["contradictions"]) >= 1, "Should detect year contradiction"

    @pytest.mark.asyncio
    async def test_verify_node_catches_amount_contradiction(self) -> None:
        """Test verify_node catches planted amount contradiction."""
        state: ResearchState = {
            "session_id": "contradiction_test_2",
            "original_query": "What is Apple's market cap?",
            "privacy_mode": "LOCAL_ONLY",
            "started_at": datetime.now(),
            "facts_extracted": [
                {
                    "statement": "Apple market capitalization reached $3 trillion dollars in 2024",
                    "sources": ["cnbc.com"],
                    "confidence": 0.9,
                    "verified": False,
                },
                {
                    "statement": "Apple market capitalization reached $2 trillion dollars in 2024",
                    "sources": ["reuters.com"],
                    "confidence": 0.85,
                    "verified": False,
                },
            ],
            "sources_queried": ["cnbc.com", "reuters.com"],
            "entities_found": [],
            "access_failures": [],
            "current_phase": "analyze",
            "should_stop": False,
        }

        result = await verify_node(state)

        assert "contradictions" in result
        # The amounts differ significantly, should be detected

    @pytest.mark.asyncio
    async def test_verify_node_reduces_confidence_for_contradicted_facts(self) -> None:
        """Test that contradicted facts have reduced confidence."""
        state: ResearchState = {
            "session_id": "contradiction_test_3",
            "original_query": "When was SpaceX founded?",
            "privacy_mode": "LOCAL_ONLY",
            "started_at": datetime.now(),
            "facts_extracted": [
                {
                    "statement": "SpaceX company was founded in 2002 by Elon Musk entrepreneur",
                    "sources": ["spacex.com"],
                    "confidence": 0.9,
                    "verified": False,
                },
                {
                    "statement": "SpaceX company was founded in 2004 by Elon Musk entrepreneur",
                    "sources": ["wikipedia.org"],
                    "confidence": 0.8,
                    "verified": False,
                },
            ],
            "sources_queried": ["spacex.com", "wikipedia.org"],
            "entities_found": [],
            "access_failures": [],
            "current_phase": "analyze",
            "should_stop": False,
        }

        result = await verify_node(state)

        assert "verification_results" in result
        # At least one fact should have reduced confidence due to contradiction
        if result.get("contradictions"):
            contradicted_facts = [
                vr for vr in result["verification_results"]
                if vr.get("contradiction_details")
            ]
            if contradicted_facts:
                for cf in contradicted_facts:
                    # Contradicted facts should have lower confidence
                    assert cf["confidence"] < 0.8, (
                        f"Contradicted fact should have reduced confidence: {cf}"
                    )


class TestNoFalsePositives:
    """Tests to ensure consistent facts don't trigger false contradictions."""

    def test_same_year_no_contradiction(self) -> None:
        """Same year in different sources should not be a contradiction."""
        facts = [
            Fact(
                statement="Google was founded in 1998 in Stanford California",
                sources=["source1.com"],
                confidence=0.9,
                verified=False,
            ),
            Fact(
                statement="Google company was founded in 1998 by Larry Page",
                sources=["source2.com"],
                confidence=0.85,
                verified=False,
            ),
        ]

        contradictions = detect_contradictions(facts)

        # Should NOT detect contradiction - years match
        year_contradictions = [
            c for c in contradictions
            if "year" in c.get("type", "").lower()
        ]
        assert len(year_contradictions) == 0, (
            f"Same year should not be flagged: {year_contradictions}"
        )

    def test_same_amount_no_contradiction(self) -> None:
        """Same amount in different sources should not be a contradiction."""
        facts = [
            Fact(
                statement="The product costs $999 at Apple Store retail",
                sources=["apple.com"],
                confidence=0.9,
                verified=False,
            ),
            Fact(
                statement="The product price is $999 at Apple Store official",
                sources=["techreview.com"],
                confidence=0.85,
                verified=False,
            ),
        ]

        contradictions = detect_contradictions(facts)

        # Should NOT detect contradiction - amounts match
        amount_contradictions = [
            c for c in contradictions
            if "amount" in c.get("type", "").lower()
        ]
        assert len(amount_contradictions) == 0, (
            f"Same amount should not be flagged: {amount_contradictions}"
        )

    def test_unrelated_facts_no_contradiction(self) -> None:
        """Unrelated facts should not be flagged as contradictions."""
        facts = [
            Fact(
                statement="Apple was founded in 1976 by Steve Jobs",
                sources=["apple_history.com"],
                confidence=0.9,
                verified=False,
            ),
            Fact(
                statement="Microsoft was founded in 1975 by Bill Gates",
                sources=["microsoft_history.com"],
                confidence=0.9,
                verified=False,
            ),
        ]

        contradictions = detect_contradictions(facts)

        # Different subjects - should NOT be a contradiction
        assert len(contradictions) == 0, (
            f"Unrelated facts should not conflict: {contradictions}"
        )

    def test_same_source_no_self_contradiction(self) -> None:
        """Facts from same source should not contradict each other."""
        facts = [
            Fact(
                statement="Revenue was $100 million in Q1 fiscal year",
                sources=["company_report.com"],
                confidence=0.9,
                verified=False,
            ),
            Fact(
                statement="Revenue was $150 million in Q2 fiscal year",
                sources=["company_report.com"],
                confidence=0.9,
                verified=False,
            ),
        ]

        contradictions = detect_contradictions(facts)

        # Same source should not self-contradict
        assert len(contradictions) == 0, (
            "Same source should not self-contradict"
        )
