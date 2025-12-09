"""Tests for synthesize agent node."""

import pytest

from research_tool.agent.nodes.synthesize import synthesize_node


class TestSynthesizeNode:
    """Test suite for synthesize_node function."""

    @pytest.mark.asyncio
    async def test_synthesize_returns_state_updates(self) -> None:
        """synthesize_node returns dict with required keys."""
        state = {
            "original_query": "test query",
            "domain": "general",
            "sources_queried": [],
            "entities_found": [],
            "facts_extracted": []
        }
        result = await synthesize_node(state)

        assert isinstance(result, dict)
        assert "final_report" in result
        assert "current_phase" in result

    @pytest.mark.asyncio
    async def test_synthesize_sets_current_phase(self) -> None:
        """synthesize_node sets current_phase to 'synthesize'."""
        state = {"original_query": "test", "domain": "general"}
        result = await synthesize_node(state)

        assert result["current_phase"] == "synthesize"

    @pytest.mark.asyncio
    async def test_synthesize_generates_report(self) -> None:
        """synthesize_node generates final report."""
        state = {
            "original_query": "test query",
            "refined_query": "refined test query",
            "domain": "medical",
            "sources_queried": ["pubmed", "arxiv"],
            "entities_found": [{"id": 1}, {"id": 2}],
            "facts_extracted": [{"statement": "fact1"}, {"statement": "fact2"}],
            "saturation_metrics": {"total": 0.8},
            "stop_reason": "Saturation reached"
        }
        result = await synthesize_node(state)

        report = result["final_report"]
        assert report["query"] == "refined test query"
        assert report["domain"] == "medical"
        assert report["sources_queried"] == 2
        assert report["entities_found"] == 2
        assert report["facts_extracted"] == 2


class TestSynthesizeReportContent:
    """Test report content generation."""

    @pytest.mark.asyncio
    async def test_report_includes_query(self) -> None:
        """Report includes the refined query."""
        state = {
            "original_query": "original",
            "refined_query": "refined query",
            "domain": "general"
        }
        result = await synthesize_node(state)

        assert result["final_report"]["query"] == "refined query"

    @pytest.mark.asyncio
    async def test_report_uses_original_if_no_refined(self) -> None:
        """Report uses original_query if refined_query not set."""
        state = {"original_query": "original query", "domain": "general"}
        result = await synthesize_node(state)

        assert result["final_report"]["query"] == "original query"

    @pytest.mark.asyncio
    async def test_report_includes_domain(self) -> None:
        """Report includes the detected domain."""
        state = {"original_query": "test", "domain": "medical"}
        result = await synthesize_node(state)

        assert result["final_report"]["domain"] == "medical"

    @pytest.mark.asyncio
    async def test_report_includes_sources_list(self) -> None:
        """Report includes list of sources queried."""
        state = {
            "original_query": "test",
            "domain": "general",
            "sources_queried": ["pubmed", "arxiv", "semantic_scholar"]
        }
        result = await synthesize_node(state)

        assert result["final_report"]["sources_list"] == ["pubmed", "arxiv", "semantic_scholar"]

    @pytest.mark.asyncio
    async def test_report_includes_stop_reason(self) -> None:
        """Report includes reason for stopping."""
        state = {
            "original_query": "test",
            "domain": "general",
            "stop_reason": "Saturation threshold reached"
        }
        result = await synthesize_node(state)

        assert result["final_report"]["stop_reason"] == "Saturation threshold reached"

    @pytest.mark.asyncio
    async def test_report_includes_saturation_metrics(self) -> None:
        """Report includes saturation metrics."""
        state = {
            "original_query": "test",
            "domain": "general",
            "saturation_metrics": {"entity_growth": 0.1, "fact_growth": 0.2}
        }
        result = await synthesize_node(state)

        assert result["final_report"]["saturation_metrics"] == {
            "entity_growth": 0.1,
            "fact_growth": 0.2
        }


class TestSynthesizeAntiPatterns:
    """Test anti-pattern prevention in synthesize node."""

    @pytest.mark.asyncio
    async def test_report_includes_limitations(self) -> None:
        """Report includes limitations (Anti-Pattern #11)."""
        state = {"original_query": "test", "domain": "general"}
        result = await synthesize_node(state)

        report = result["final_report"]
        assert "limitations" in report
        assert len(report["limitations"]) > 0

    @pytest.mark.asyncio
    async def test_report_limitations_are_meaningful(self) -> None:
        """Report limitations contain useful information."""
        state = {"original_query": "test", "domain": "general"}
        result = await synthesize_node(state)

        limitations = result["final_report"]["limitations"]
        # Check that limitations are strings with content
        for limitation in limitations:
            assert isinstance(limitation, str)
            assert len(limitation) > 5

    @pytest.mark.asyncio
    async def test_report_includes_summary(self) -> None:
        """Report includes summary of findings."""
        state = {"original_query": "test query", "domain": "general"}
        result = await synthesize_node(state)

        assert "summary" in result["final_report"]
        assert "test query" in result["final_report"]["summary"]

    @pytest.mark.asyncio
    async def test_report_limits_findings_to_20(self) -> None:
        """Report limits findings to top 20 facts."""
        state = {
            "original_query": "test",
            "domain": "general",
            "facts_extracted": [{"statement": f"fact{i}"} for i in range(50)]
        }
        result = await synthesize_node(state)

        assert len(result["final_report"]["findings"]) == 20


class TestSynthesizeEdgeCases:
    """Test edge cases in synthesize node."""

    @pytest.mark.asyncio
    async def test_synthesize_handles_empty_state(self) -> None:
        """synthesize_node handles minimal state."""
        state = {"original_query": "test"}
        result = await synthesize_node(state)

        report = result["final_report"]
        assert report["sources_queried"] == 0
        assert report["entities_found"] == 0
        assert report["facts_extracted"] == 0

    @pytest.mark.asyncio
    async def test_synthesize_handles_none_values(self) -> None:
        """synthesize_node handles None values in state."""
        state = {
            "original_query": "test",
            "domain": None,
            "saturation_metrics": None,
            "stop_reason": None
        }
        result = await synthesize_node(state)

        # Should not crash
        assert result["final_report"] is not None
