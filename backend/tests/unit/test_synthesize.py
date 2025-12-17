"""Tests for synthesize agent node."""

from unittest.mock import AsyncMock, patch

import pytest

from research_tool.agent.nodes.synthesize import (
    generate_executive_summary,
    generate_limitations,
    synthesize_node,
)


class TestSynthesizeNode:
    """Test suite for synthesize_node function."""

    @pytest.mark.asyncio
    async def test_synthesize_returns_state_updates(self) -> None:
        """synthesize_node returns dict with required keys."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Test summary")
            mock_get_router.return_value = mock_router

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
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Summary")
            mock_get_router.return_value = mock_router

            state = {"original_query": "test", "domain": "general"}
            result = await synthesize_node(state)

            assert result["current_phase"] == "synthesize"

    @pytest.mark.asyncio
    async def test_synthesize_generates_report(self) -> None:
        """synthesize_node generates final report with correct structure."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Generated summary")
            mock_get_router.return_value = mock_router

            state = {
                "original_query": "test query",
                "refined_query": "refined test query",
                "domain": "medical",
                "sources_queried": ["pubmed", "arxiv"],
                "entities_found": [{"url": "url1"}, {"url": "url2"}],
                "facts_extracted": [
                    {"statement": "fact1", "confidence": 0.8},
                    {"statement": "fact2", "confidence": 0.7}
                ],
                "saturation_metrics": {"total": 0.8},
                "stop_reason": "Saturation reached"
            }
            result = await synthesize_node(state)

            report = result["final_report"]
            assert report["query"] == "refined test query"
            assert report["domain"] == "medical"
            # Methodology is nested
            assert report["methodology"]["sources_queried"] == ["pubmed", "arxiv"]
            assert report["methodology"]["entities_found"] == 2
            assert report["methodology"]["facts_extracted"] == 2


class TestSynthesizeReportContent:
    """Test report content generation."""

    @pytest.mark.asyncio
    async def test_report_includes_query(self) -> None:
        """Report includes the refined query."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Summary")
            mock_get_router.return_value = mock_router

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
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Summary")
            mock_get_router.return_value = mock_router

            state = {"original_query": "original query", "domain": "general"}
            result = await synthesize_node(state)

            assert result["final_report"]["query"] == "original query"

    @pytest.mark.asyncio
    async def test_report_includes_domain(self) -> None:
        """Report includes the detected domain."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Summary")
            mock_get_router.return_value = mock_router

            state = {"original_query": "test", "domain": "medical"}
            result = await synthesize_node(state)

            assert result["final_report"]["domain"] == "medical"

    @pytest.mark.asyncio
    async def test_report_includes_sources_in_methodology(self) -> None:
        """Report includes sources_queried in methodology."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Summary")
            mock_get_router.return_value = mock_router

            state = {
                "original_query": "test",
                "domain": "general",
                "sources_queried": ["pubmed", "arxiv", "semantic_scholar"]
            }
            result = await synthesize_node(state)

            methodology = result["final_report"]["methodology"]
            assert methodology["sources_queried"] == ["pubmed", "arxiv", "semantic_scholar"]

    @pytest.mark.asyncio
    async def test_report_includes_stop_reason_in_methodology(self) -> None:
        """Report includes stop_reason in methodology."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Summary")
            mock_get_router.return_value = mock_router

            state = {
                "original_query": "test",
                "domain": "general",
                "stop_reason": "Saturation threshold reached"
            }
            result = await synthesize_node(state)

            methodology = result["final_report"]["methodology"]
            assert methodology["stop_reason"] == "Saturation threshold reached"

    @pytest.mark.asyncio
    async def test_report_includes_saturation_in_methodology(self) -> None:
        """Report includes saturation_metrics in methodology."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Summary")
            mock_get_router.return_value = mock_router

            state = {
                "original_query": "test",
                "domain": "general",
                "saturation_metrics": {"entity_growth": 0.1, "fact_growth": 0.2}
            }
            result = await synthesize_node(state)

            methodology = result["final_report"]["methodology"]
            assert methodology["saturation_metrics"] == {
                "entity_growth": 0.1,
                "fact_growth": 0.2
            }


class TestSynthesizeAntiPatterns:
    """Test anti-pattern prevention in synthesize node."""

    @pytest.mark.asyncio
    async def test_report_includes_limitations(self) -> None:
        """Report includes limitations (Anti-Pattern #11)."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Summary")
            mock_get_router.return_value = mock_router

            state = {"original_query": "test", "domain": "general"}
            result = await synthesize_node(state)

            report = result["final_report"]
            assert "limitations" in report
            assert len(report["limitations"]) > 0

    @pytest.mark.asyncio
    async def test_report_limitations_are_meaningful(self) -> None:
        """Report limitations contain useful information."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Summary")
            mock_get_router.return_value = mock_router

            state = {"original_query": "test", "domain": "general"}
            result = await synthesize_node(state)

            limitations = result["final_report"]["limitations"]
            # Check that limitations are strings with content
            for limitation in limitations:
                assert isinstance(limitation, str)
                assert len(limitation) > 5

    @pytest.mark.asyncio
    async def test_report_includes_summary(self) -> None:
        """Report includes LLM-generated summary."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="This is the LLM summary")
            mock_get_router.return_value = mock_router

            state = {"original_query": "test query", "domain": "general"}
            result = await synthesize_node(state)

            assert "summary" in result["final_report"]
            # Summary is LLM-generated, check it exists
            assert len(result["final_report"]["summary"]) > 0

    @pytest.mark.asyncio
    async def test_report_limits_findings_to_20(self) -> None:
        """Report limits findings to top 20 facts."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Summary")
            mock_get_router.return_value = mock_router

            state = {
                "original_query": "test",
                "domain": "general",
                "facts_extracted": [
                    {"statement": f"fact{i}", "confidence": 0.5}
                    for i in range(50)
                ]
            }
            result = await synthesize_node(state)

            assert len(result["final_report"]["findings"]) == 20


class TestSynthesizeEdgeCases:
    """Test edge cases in synthesize node."""

    @pytest.mark.asyncio
    async def test_synthesize_handles_empty_state(self) -> None:
        """synthesize_node handles minimal state."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Summary for empty results")
            mock_get_router.return_value = mock_router

            state = {"original_query": "test"}
            result = await synthesize_node(state)

            report = result["final_report"]
            methodology = report["methodology"]
            assert methodology["sources_queried"] == []
            assert methodology["entities_found"] == 0
            assert methodology["facts_extracted"] == 0

    @pytest.mark.asyncio
    async def test_synthesize_handles_none_values(self) -> None:
        """synthesize_node handles None values in state."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="Summary")
            mock_get_router.return_value = mock_router

            state = {
                "original_query": "test",
                "domain": None,
                "saturation_metrics": None,
                "stop_reason": None
            }
            result = await synthesize_node(state)

            # Should not crash
            assert result["final_report"] is not None


class TestGenerateExecutiveSummary:
    """Test generate_executive_summary function."""

    @pytest.mark.asyncio
    async def test_summary_handles_empty_facts(self) -> None:
        """generate_executive_summary handles empty facts list."""
        result = await generate_executive_summary("test query", [], "general")
        assert "No facts were extracted" in result

    @pytest.mark.asyncio
    async def test_summary_calls_llm_with_facts(self) -> None:
        """generate_executive_summary calls LLM when facts exist."""
        with patch(
            "research_tool.agent.nodes.synthesize.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value="LLM generated summary")
            mock_get_router.return_value = mock_router

            facts = [{"statement": "Test fact", "confidence": 0.9}]
            result = await generate_executive_summary("query", facts, "general")

            assert result == "LLM generated summary"
            mock_router.complete.assert_called_once()


class TestGenerateLimitations:
    """Test generate_limitations function."""

    def test_limitations_for_medical_domain(self) -> None:
        """generate_limitations includes medical disclaimer."""
        limitations = generate_limitations(["pubmed"], [], "medical")
        medical_found = any("medical" in lim.lower() for lim in limitations)
        assert medical_found

    def test_limitations_for_academic_domain(self) -> None:
        """generate_limitations includes academic disclaimer."""
        limitations = generate_limitations(["arxiv"], [], "academic")
        academic_found = any("academic" in lim.lower() for lim in limitations)
        assert academic_found

    def test_limitations_notes_contradictions(self) -> None:
        """generate_limitations notes when contradictions exist."""
        contradictions = [{"type": "year_conflict"}]
        limitations = generate_limitations([], contradictions, "general")
        contradiction_found = any("contradict" in lim.lower() for lim in limitations)
        assert contradiction_found

    def test_limitations_notes_missing_sources(self) -> None:
        """generate_limitations notes missing sources."""
        # Only queried one source
        limitations = generate_limitations(["pubmed"], [], "general")
        missing_found = any("not all sources" in lim.lower() for lim in limitations)
        assert missing_found
