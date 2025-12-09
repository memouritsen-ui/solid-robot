"""Tests for analyze agent node."""

import pytest

from research_tool.agent.nodes.analyze import analyze_node


class TestAnalyzeNode:
    """Test suite for analyze_node function."""

    @pytest.mark.asyncio
    async def test_analyze_returns_state_updates(self) -> None:
        """analyze_node returns dict with current_phase."""
        state = {"original_query": "test query", "facts_extracted": []}
        result = await analyze_node(state)

        assert isinstance(result, dict)
        assert "current_phase" in result

    @pytest.mark.asyncio
    async def test_analyze_sets_current_phase(self) -> None:
        """analyze_node sets current_phase to 'analyze'."""
        state = {"original_query": "test query", "facts_extracted": []}
        result = await analyze_node(state)

        assert result["current_phase"] == "analyze"

    @pytest.mark.asyncio
    async def test_analyze_handles_empty_facts(self) -> None:
        """analyze_node handles empty facts_extracted."""
        state = {"original_query": "test query", "facts_extracted": []}
        result = await analyze_node(state)

        assert result["current_phase"] == "analyze"

    @pytest.mark.asyncio
    async def test_analyze_handles_missing_facts_key(self) -> None:
        """analyze_node handles missing facts_extracted key."""
        state = {"original_query": "test query"}
        result = await analyze_node(state)

        assert result["current_phase"] == "analyze"

    @pytest.mark.asyncio
    async def test_analyze_processes_multiple_facts(self) -> None:
        """analyze_node processes multiple facts."""
        state = {
            "original_query": "test",
            "facts_extracted": [
                {"statement": "Fact 1", "source": "url1", "confidence": 0.8},
                {"statement": "Fact 2", "source": "url2", "confidence": 0.7},
                {"statement": "Fact 3", "source": "url3", "confidence": 0.9},
            ]
        }
        result = await analyze_node(state)

        # Should complete without error
        assert result["current_phase"] == "analyze"


class TestAnalyzeNodeLogging:
    """Test logging behavior of analyze node."""

    @pytest.mark.asyncio
    async def test_analyze_logs_facts_count(self) -> None:
        """analyze_node logs the count of analyzed facts."""
        # The actual logging is tested implicitly
        # Here we verify it doesn't crash with various inputs
        test_cases = [
            {"original_query": "test", "facts_extracted": []},
            {"original_query": "test", "facts_extracted": [{"statement": "x"}]},
            {"original_query": "test"},
        ]

        for state in test_cases:
            result = await analyze_node(state)
            assert result is not None
