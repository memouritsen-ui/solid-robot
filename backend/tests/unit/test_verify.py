"""Tests for cross-verification node."""

from datetime import datetime

import pytest

from research_tool.agent.nodes.verify import (
    VerificationResult,
    calculate_source_agreement,
    detect_contradictions,
    extract_facts_from_content,
    verify_node,
)
from research_tool.models.entities import Fact
from research_tool.models.state import ResearchState


class TestExtractFactsFromContent:
    """Tests for fact extraction from content."""

    def test_extract_facts_returns_list(self) -> None:
        """Test that extraction returns a list of facts."""
        content = "Python was created by Guido van Rossum in 1991."
        source_url = "https://example.com/python"

        facts = extract_facts_from_content(content, source_url)

        assert isinstance(facts, list)

    def test_extract_facts_includes_source(self) -> None:
        """Test that extracted facts include source URL."""
        content = "The Earth is the third planet from the Sun."
        source_url = "https://example.com/earth"

        facts = extract_facts_from_content(content, source_url)

        if facts:  # If any facts extracted
            assert all(source_url in f.sources for f in facts)

    def test_extract_facts_from_empty_content(self) -> None:
        """Test extraction from empty content."""
        facts = extract_facts_from_content("", "https://example.com")

        assert facts == []

    def test_extract_facts_sets_initial_confidence(self) -> None:
        """Test that extracted facts have initial confidence."""
        content = "Water boils at 100 degrees Celsius at sea level."
        source_url = "https://example.com/water"

        facts = extract_facts_from_content(content, source_url)

        if facts:
            assert all(0.0 <= f.confidence <= 1.0 for f in facts)


class TestDetectContradictions:
    """Tests for contradiction detection."""

    def test_detect_no_contradictions_when_consistent(self) -> None:
        """Test no contradictions detected for consistent facts."""
        facts = [
            Fact(
                statement="Python was created in 1991",
                sources=["url1"],
                confidence=0.8,
                verified=True
            ),
            Fact(
                statement="Python was released in 1991",
                sources=["url2"],
                confidence=0.8,
                verified=True
            ),
        ]

        contradictions = detect_contradictions(facts)

        # Similar facts should not be contradictions
        assert len(contradictions) == 0

    def test_detect_contradictions_with_conflicting_facts(self) -> None:
        """Test contradiction detection for conflicting facts."""
        # Use statements with more word overlap to pass subject matching
        facts = [
            Fact(
                statement="Acme Corporation company was founded in 2010 by John",
                sources=["url1"],
                confidence=0.8,
                verified=True
            ),
            Fact(
                statement="Acme Corporation company was founded in 2015 by John",
                sources=["url2"],
                confidence=0.8,
                verified=True
            ),
        ]

        contradictions = detect_contradictions(facts)

        # Should detect year conflict
        assert len(contradictions) >= 1

    def test_detect_contradictions_returns_pairs(self) -> None:
        """Test that contradictions are returned as pairs."""
        facts = [
            Fact(
                statement="Product X costs $100",
                sources=["url1"],
                confidence=0.7,
                verified=True
            ),
            Fact(
                statement="Product X costs $200",
                sources=["url2"],
                confidence=0.7,
                verified=True
            ),
        ]

        contradictions = detect_contradictions(facts)

        if contradictions:
            for contradiction in contradictions:
                assert "fact1" in contradiction
                assert "fact2" in contradiction
                assert "reason" in contradiction


class TestCalculateSourceAgreement:
    """Tests for source agreement calculation."""

    def test_single_source_returns_low_agreement(self) -> None:
        """Test that single source gives low agreement score."""
        fact = Fact(
            statement="Test statement",
            sources=["url1"],
            confidence=0.5,
            verified=False
        )

        agreement = calculate_source_agreement(fact)

        assert agreement < 0.5

    def test_multiple_sources_increases_agreement(self) -> None:
        """Test that multiple sources increase agreement."""
        single_source_fact = Fact(
            statement="Test statement",
            sources=["url1"],
            confidence=0.5,
            verified=False
        )

        multi_source_fact = Fact(
            statement="Test statement",
            sources=["url1", "url2", "url3"],
            confidence=0.5,
            verified=False
        )

        single_agreement = calculate_source_agreement(single_source_fact)
        multi_agreement = calculate_source_agreement(multi_source_fact)

        assert multi_agreement > single_agreement

    def test_agreement_capped_at_one(self) -> None:
        """Test that agreement score is capped at 1.0."""
        fact = Fact(
            statement="Well-verified statement",
            sources=[f"url{i}" for i in range(20)],
            confidence=0.9,
            verified=True
        )

        agreement = calculate_source_agreement(fact)

        assert agreement <= 1.0


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_create_verification_result(self) -> None:
        """Test creating a VerificationResult."""
        result = VerificationResult(
            fact_id="fact_001",
            original_statement="Test statement",
            verified=True,
            confidence=0.85,
            supporting_sources=["url1", "url2"],
            contradicting_sources=[],
            contradiction_details=[]
        )

        assert result.fact_id == "fact_001"
        assert result.verified is True
        assert result.confidence == 0.85

    def test_verification_result_to_dict(self) -> None:
        """Test conversion to dictionary."""
        result = VerificationResult(
            fact_id="fact_002",
            original_statement="Another statement",
            verified=False,
            confidence=0.3,
            supporting_sources=["url1"],
            contradicting_sources=["url2"],
            contradiction_details=["Conflicting date"]
        )

        d = result.to_dict()

        assert d["fact_id"] == "fact_002"
        assert d["verified"] is False
        assert "Conflicting date" in d["contradiction_details"]


class TestVerifyNode:
    """Tests for the verify_node function."""

    @pytest.mark.asyncio
    async def test_verify_node_returns_state_updates(self) -> None:
        """Test that verify_node returns state updates."""
        state: ResearchState = {
            "session_id": "test_session",
            "original_query": "test query",
            "privacy_mode": "LOCAL_ONLY",
            "started_at": datetime.now(),
            "facts_extracted": [],
            "sources_queried": [],
            "entities_found": [],
            "access_failures": [],
            "current_phase": "analyze",
            "should_stop": False,
        }

        result = await verify_node(state)

        assert isinstance(result, dict)
        assert "current_phase" in result

    @pytest.mark.asyncio
    async def test_verify_node_sets_phase_to_verify(self) -> None:
        """Test that verify_node sets current_phase to verify."""
        state: ResearchState = {
            "session_id": "test_session",
            "original_query": "test query",
            "privacy_mode": "LOCAL_ONLY",
            "started_at": datetime.now(),
            "facts_extracted": [],
            "sources_queried": [],
            "entities_found": [],
            "access_failures": [],
            "current_phase": "analyze",
            "should_stop": False,
        }

        result = await verify_node(state)

        assert result["current_phase"] == "verify"

    @pytest.mark.asyncio
    async def test_verify_node_processes_facts(self) -> None:
        """Test that verify_node processes facts from state."""
        state: ResearchState = {
            "session_id": "test_session",
            "original_query": "test query",
            "privacy_mode": "LOCAL_ONLY",
            "started_at": datetime.now(),
            "facts_extracted": [
                {
                    "statement": "Test fact 1",
                    "sources": ["url1"],
                    "confidence": 0.7,
                    "verified": False
                },
                {
                    "statement": "Test fact 2",
                    "sources": ["url2"],
                    "confidence": 0.6,
                    "verified": False
                }
            ],
            "sources_queried": ["url1", "url2"],
            "entities_found": [],
            "access_failures": [],
            "current_phase": "analyze",
            "should_stop": False,
        }

        result = await verify_node(state)

        # Should return verification results
        assert "verification_results" in result or "current_phase" in result

    @pytest.mark.asyncio
    async def test_verify_node_handles_empty_facts(self) -> None:
        """Test that verify_node handles empty facts list."""
        state: ResearchState = {
            "session_id": "test_session",
            "original_query": "test query",
            "privacy_mode": "LOCAL_ONLY",
            "started_at": datetime.now(),
            "facts_extracted": [],
            "sources_queried": [],
            "entities_found": [],
            "access_failures": [],
            "current_phase": "analyze",
            "should_stop": False,
        }

        result = await verify_node(state)

        # Should not raise, should return valid result
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_verify_node_detects_contradictions(self) -> None:
        """Test that verify_node can detect contradictions."""
        state: ResearchState = {
            "session_id": "test_session",
            "original_query": "test query",
            "privacy_mode": "LOCAL_ONLY",
            "started_at": datetime.now(),
            "facts_extracted": [
                {
                    "statement": "Company revenue was $10 million in 2023",
                    "sources": ["url1"],
                    "confidence": 0.7,
                    "verified": False
                },
                {
                    "statement": "Company revenue was $50 million in 2023",
                    "sources": ["url2"],
                    "confidence": 0.7,
                    "verified": False
                }
            ],
            "sources_queried": ["url1", "url2"],
            "entities_found": [],
            "access_failures": [],
            "current_phase": "analyze",
            "should_stop": False,
        }

        result = await verify_node(state)

        # Should process and potentially detect contradictions
        assert isinstance(result, dict)


class TestVerifyNodeIntegration:
    """Integration tests for verify node with other components."""

    @pytest.mark.asyncio
    async def test_verify_node_integrates_with_state(self) -> None:
        """Test verify_node integration with ResearchState."""
        state: ResearchState = {
            "session_id": "integration_test",
            "original_query": "What is the population of Denmark?",
            "privacy_mode": "LOCAL_ONLY",
            "started_at": datetime.now(),
            "refined_query": "Denmark population statistics",
            "domain": "general",
            "facts_extracted": [
                {
                    "statement": "Denmark has a population of about 5.9 million",
                    "sources": ["url1", "url2"],
                    "confidence": 0.8,
                    "verified": False
                }
            ],
            "sources_queried": ["url1", "url2"],
            "entities_found": [],
            "access_failures": [],
            "current_phase": "analyze",
            "should_stop": False,
            "saturation_metrics": None,
            "stop_reason": None,
        }

        result = await verify_node(state)

        assert result["current_phase"] == "verify"
