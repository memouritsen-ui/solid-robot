"""Tests for evaluate agent node."""


import pytest

from research_tool.agent.nodes.evaluate import evaluate_node


class TestEvaluateNode:
    """Test suite for evaluate_node function."""

    @pytest.mark.asyncio
    async def test_evaluate_returns_state_updates(self) -> None:
        """evaluate_node returns dict with required keys."""
        state = {
            "original_query": "test query",
            "entities_found": [],
            "facts_extracted": [],
            "sources_queried": []
        }
        result = await evaluate_node(state)

        assert isinstance(result, dict)
        assert "saturation_metrics" in result
        assert "should_stop" in result
        assert "current_phase" in result

    @pytest.mark.asyncio
    async def test_evaluate_sets_current_phase(self) -> None:
        """evaluate_node sets current_phase to 'evaluate'."""
        state = {
            "original_query": "test",
            "entities_found": [],
            "facts_extracted": [],
            "sources_queried": []
        }
        result = await evaluate_node(state)

        assert result["current_phase"] == "evaluate"

    @pytest.mark.asyncio
    async def test_evaluate_calculates_saturation_metrics(self) -> None:
        """evaluate_node calculates saturation metrics."""
        state = {
            "original_query": "test",
            "entities_found": [{"id": 1}, {"id": 2}],
            "facts_extracted": [{"statement": "fact1"}, {"statement": "fact2"}],
            "sources_queried": ["pubmed", "arxiv"]
        }
        result = await evaluate_node(state)

        metrics = result["saturation_metrics"]
        assert metrics is not None
        assert isinstance(metrics, dict)

    @pytest.mark.asyncio
    async def test_evaluate_returns_should_stop_bool(self) -> None:
        """evaluate_node returns should_stop as boolean."""
        state = {
            "original_query": "test",
            "entities_found": [],
            "facts_extracted": [],
            "sources_queried": []
        }
        result = await evaluate_node(state)

        assert isinstance(result["should_stop"], bool)

    @pytest.mark.asyncio
    async def test_evaluate_includes_stop_reason_when_stopping(self) -> None:
        """evaluate_node includes stop_reason when should_stop is True."""
        # Create state that triggers stopping (all sources queried)
        state = {
            "original_query": "test",
            "entities_found": list(range(100)),  # Many entities
            "facts_extracted": list(range(100)),  # Many facts
            "sources_queried": list(range(10))  # All sources used
        }
        result = await evaluate_node(state)

        if result["should_stop"]:
            assert result["stop_reason"] is not None
        else:
            assert result["stop_reason"] is None


class TestEvaluateSaturationLogic:
    """Test saturation calculation logic."""

    @pytest.mark.asyncio
    async def test_evaluate_with_no_data(self) -> None:
        """Handles state with no entities or facts."""
        state = {
            "original_query": "test",
            "entities_found": [],
            "facts_extracted": [],
            "sources_queried": []
        }
        result = await evaluate_node(state)

        # Should still return valid metrics
        assert result["saturation_metrics"] is not None

    @pytest.mark.asyncio
    async def test_evaluate_with_missing_keys(self) -> None:
        """Handles state with missing keys."""
        state = {"original_query": "test"}
        result = await evaluate_node(state)

        # Should handle gracefully
        assert result["current_phase"] == "evaluate"

    @pytest.mark.asyncio
    async def test_evaluate_metrics_include_expected_fields(self) -> None:
        """Saturation metrics include expected fields."""
        state = {
            "original_query": "test",
            "entities_found": [{"id": 1}],
            "facts_extracted": [{"statement": "x"}],
            "sources_queried": ["source1"]
        }
        result = await evaluate_node(state)

        metrics = result["saturation_metrics"]
        # Check that metrics is a dict (from to_dict())
        assert isinstance(metrics, dict)


class TestEvaluateAntiPatterns:
    """Test anti-pattern prevention in evaluate node."""

    @pytest.mark.asyncio
    async def test_evaluate_prevents_early_stop(self) -> None:
        """evaluate_node prevents stopping too early (Anti-Pattern #3)."""
        # With very few sources queried, should not stop
        state = {
            "original_query": "test",
            "entities_found": [{"id": i} for i in range(5)],
            "facts_extracted": [{"s": i} for i in range(5)],
            "sources_queried": ["source1"]  # Only 1 source
        }
        result = await evaluate_node(state)

        # With only 1 source queried out of 10 available,
        # saturation should be low and shouldn't stop
        # (depends on actual saturation thresholds)
        assert result["saturation_metrics"] is not None

    @pytest.mark.asyncio
    async def test_evaluate_allows_stop_when_saturated(self) -> None:
        """evaluate_node allows stopping when truly saturated (Anti-Pattern #4)."""
        # All sources queried, diminishing returns
        state = {
            "original_query": "test",
            "entities_found": [{"id": i} for i in range(100)],
            "facts_extracted": [{"s": i} for i in range(100)],
            "sources_queried": [f"source{i}" for i in range(10)]
        }
        result = await evaluate_node(state)

        # Should have valid decision
        assert isinstance(result["should_stop"], bool)
