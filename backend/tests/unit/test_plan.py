"""Tests for plan agent node."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research_tool.agent.nodes.plan import plan_node


class TestPlanNode:
    """Test suite for plan_node function."""

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.plan.CombinedMemoryRepository")
    async def test_plan_returns_state_updates(
        self, mock_memory_class: MagicMock
    ) -> None:
        """plan_node returns dict with current_phase."""
        mock_memory = MagicMock()
        mock_memory.initialize = AsyncMock()
        mock_memory.search_similar = AsyncMock(return_value=[])
        mock_memory.get_ranked_sources = AsyncMock(return_value=[])
        mock_memory.get_failed_urls = AsyncMock(return_value=[])
        mock_memory_class.return_value = mock_memory

        state = {"original_query": "test query"}
        result = await plan_node(state)

        assert isinstance(result, dict)
        assert "current_phase" in result
        assert result["current_phase"] == "plan"

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.plan.CombinedMemoryRepository")
    async def test_plan_initializes_memory(
        self, mock_memory_class: MagicMock
    ) -> None:
        """plan_node initializes memory repository."""
        mock_memory = MagicMock()
        mock_memory.initialize = AsyncMock()
        mock_memory.search_similar = AsyncMock(return_value=[])
        mock_memory.get_ranked_sources = AsyncMock(return_value=[])
        mock_memory.get_failed_urls = AsyncMock(return_value=[])
        mock_memory_class.return_value = mock_memory

        state = {"original_query": "test query"}
        await plan_node(state)

        mock_memory.initialize.assert_called_once()

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.plan.CombinedMemoryRepository")
    async def test_plan_searches_past_research(
        self, mock_memory_class: MagicMock
    ) -> None:
        """plan_node searches for similar past research."""
        mock_memory = MagicMock()
        mock_memory.initialize = AsyncMock()
        mock_memory.search_similar = AsyncMock(return_value=[])
        mock_memory.get_ranked_sources = AsyncMock(return_value=[])
        mock_memory.get_failed_urls = AsyncMock(return_value=[])
        mock_memory_class.return_value = mock_memory

        state = {"original_query": "test query", "refined_query": "refined test"}
        await plan_node(state)

        mock_memory.search_similar.assert_called_once_with("refined test", limit=3)

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.plan.CombinedMemoryRepository")
    async def test_plan_uses_original_query_if_no_refined(
        self, mock_memory_class: MagicMock
    ) -> None:
        """Uses original_query for search when refined_query not set."""
        mock_memory = MagicMock()
        mock_memory.initialize = AsyncMock()
        mock_memory.search_similar = AsyncMock(return_value=[])
        mock_memory.get_ranked_sources = AsyncMock(return_value=[])
        mock_memory.get_failed_urls = AsyncMock(return_value=[])
        mock_memory_class.return_value = mock_memory

        state = {"original_query": "test query"}
        await plan_node(state)

        mock_memory.search_similar.assert_called_once_with("test query", limit=3)


class TestPlanDomainConfiguration:
    """Test domain configuration in plan node."""

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.plan.CombinedMemoryRepository")
    @patch("research_tool.agent.nodes.plan.DomainConfiguration")
    async def test_plan_uses_medical_config(
        self, mock_config: MagicMock, mock_memory_class: MagicMock
    ) -> None:
        """Uses medical configuration for medical domain."""
        mock_memory = MagicMock()
        mock_memory.initialize = AsyncMock()
        mock_memory.search_similar = AsyncMock(return_value=[])
        mock_memory.get_ranked_sources = AsyncMock(return_value=[])
        mock_memory.get_failed_urls = AsyncMock(return_value=[])
        mock_memory_class.return_value = mock_memory

        mock_config.for_medical.return_value = MagicMock(
            primary_sources=["pubmed"],
            secondary_sources=[]
        )

        state = {"original_query": "test", "domain": "medical"}
        await plan_node(state)

        mock_config.for_medical.assert_called_once()

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.plan.CombinedMemoryRepository")
    @patch("research_tool.agent.nodes.plan.DomainConfiguration")
    async def test_plan_uses_default_for_unknown_domain(
        self, mock_config: MagicMock, mock_memory_class: MagicMock
    ) -> None:
        """Uses default configuration for unknown domain."""
        mock_memory = MagicMock()
        mock_memory.initialize = AsyncMock()
        mock_memory.search_similar = AsyncMock(return_value=[])
        mock_memory.get_ranked_sources = AsyncMock(return_value=[])
        mock_memory.get_failed_urls = AsyncMock(return_value=[])
        mock_memory_class.return_value = mock_memory

        mock_config.default.return_value = MagicMock(
            primary_sources=["tavily"],
            secondary_sources=[]
        )

        state = {"original_query": "test", "domain": "unknown_domain"}
        await plan_node(state)

        mock_config.default.assert_called_once()

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.plan.CombinedMemoryRepository")
    async def test_plan_gets_ranked_sources(
        self, mock_memory_class: MagicMock
    ) -> None:
        """plan_node gets ranked sources from memory."""
        mock_memory = MagicMock()
        mock_memory.initialize = AsyncMock()
        mock_memory.search_similar = AsyncMock(return_value=[])
        mock_memory.get_ranked_sources = AsyncMock(
            return_value=[("pubmed", 0.9), ("arxiv", 0.8)]
        )
        mock_memory.get_failed_urls = AsyncMock(return_value=[])
        mock_memory_class.return_value = mock_memory

        state = {"original_query": "test", "domain": "medical"}
        await plan_node(state)

        mock_memory.get_ranked_sources.assert_called_once()

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.plan.CombinedMemoryRepository")
    async def test_plan_gets_failed_urls(
        self, mock_memory_class: MagicMock
    ) -> None:
        """plan_node retrieves list of failed URLs to avoid."""
        mock_memory = MagicMock()
        mock_memory.initialize = AsyncMock()
        mock_memory.search_similar = AsyncMock(return_value=[])
        mock_memory.get_ranked_sources = AsyncMock(return_value=[])
        mock_memory.get_failed_urls = AsyncMock(
            return_value=["http://failed.com"]
        )
        mock_memory_class.return_value = mock_memory

        state = {"original_query": "test"}
        await plan_node(state)

        mock_memory.get_failed_urls.assert_called_once()
