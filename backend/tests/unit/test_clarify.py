"""Tests for clarify agent node."""


import pytest

from research_tool.agent.nodes.clarify import clarify_node


class TestClarifyNode:
    """Test suite for clarify_node function."""

    @pytest.mark.asyncio
    async def test_clarify_returns_state_updates(self) -> None:
        """clarify_node returns dict with required keys."""
        state = {"original_query": "test query"}
        result = await clarify_node(state)

        assert isinstance(result, dict)
        assert "refined_query" in result
        assert "domain" in result
        assert "current_phase" in result

    @pytest.mark.asyncio
    async def test_clarify_sets_current_phase(self) -> None:
        """clarify_node sets current_phase to 'clarify'."""
        state = {"original_query": "test query"}
        result = await clarify_node(state)

        assert result["current_phase"] == "clarify"

    @pytest.mark.asyncio
    async def test_clarify_uses_original_query_if_no_refined(self) -> None:
        """Uses original_query when refined_query not present."""
        state = {"original_query": "test query"}
        result = await clarify_node(state)

        assert result["refined_query"] == "test query"

    @pytest.mark.asyncio
    async def test_clarify_preserves_existing_refined_query(self) -> None:
        """Preserves refined_query if already set."""
        state = {
            "original_query": "original",
            "refined_query": "refined"
        }
        result = await clarify_node(state)

        assert result["refined_query"] == "refined"


class TestDomainDetection:
    """Test domain detection in clarify node."""

    @pytest.mark.asyncio
    async def test_detects_medical_domain(self) -> None:
        """Detects medical domain from keywords."""
        medical_queries = [
            "treatment options for diabetes",
            "clinical trial results for cancer",
            "patient outcomes in surgery",
            "disease progression in elderly"
        ]

        for query in medical_queries:
            state = {"original_query": query}
            result = await clarify_node(state)
            assert result["domain"] == "medical", f"Failed for: {query}"

    @pytest.mark.asyncio
    async def test_detects_competitive_intelligence_domain(self) -> None:
        """Detects competitive intelligence domain from keywords."""
        ci_queries = [
            "company market analysis",
            "competitor pricing strategy",
            "startup funding rounds",
            "market share trends"
        ]

        for query in ci_queries:
            state = {"original_query": query}
            result = await clarify_node(state)
            assert result["domain"] == "competitive_intelligence", f"Failed for: {query}"

    @pytest.mark.asyncio
    async def test_detects_academic_domain(self) -> None:
        """Detects academic domain from keywords."""
        academic_queries = [
            "research on machine learning",
            "academic paper review",
            "study methodology analysis"
        ]

        for query in academic_queries:
            state = {"original_query": query}
            result = await clarify_node(state)
            assert result["domain"] == "academic", f"Failed for: {query}"

    @pytest.mark.asyncio
    async def test_detects_regulatory_domain(self) -> None:
        """Detects regulatory domain from keywords."""
        regulatory_queries = [
            "regulation compliance requirements",
            "new law affecting industry",
            "policy changes in healthcare"
        ]

        for query in regulatory_queries:
            state = {"original_query": query}
            result = await clarify_node(state)
            assert result["domain"] == "regulatory", f"Failed for: {query}"

    @pytest.mark.asyncio
    async def test_defaults_to_general_domain(self) -> None:
        """Defaults to general domain for unrecognized queries."""
        state = {"original_query": "random stuff about nothing specific"}
        result = await clarify_node(state)

        assert result["domain"] == "general"

    @pytest.mark.asyncio
    async def test_domain_detection_case_insensitive(self) -> None:
        """Domain detection is case insensitive."""
        state = {"original_query": "MEDICAL TREATMENT OPTIONS"}
        result = await clarify_node(state)

        assert result["domain"] == "medical"
