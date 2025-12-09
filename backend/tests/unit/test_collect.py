"""Tests for collect agent node."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research_tool.agent.nodes.collect import collect_node, get_crawler


class TestGetCrawler:
    """Test crawler singleton."""

    def test_get_crawler_returns_instance(self) -> None:
        """get_crawler returns a crawler instance."""
        # Reset global
        import research_tool.agent.nodes.collect as collect_module
        collect_module._crawler = None

        with patch("research_tool.agent.nodes.collect.PlaywrightCrawler") as mock:
            mock.return_value = MagicMock()
            crawler = get_crawler()
            assert crawler is not None

    def test_get_crawler_reuses_instance(self) -> None:
        """get_crawler reuses existing instance."""
        import research_tool.agent.nodes.collect as collect_module
        collect_module._crawler = None

        with patch("research_tool.agent.nodes.collect.PlaywrightCrawler") as mock:
            mock.return_value = MagicMock()
            crawler1 = get_crawler()
            crawler2 = get_crawler()
            assert crawler1 is crawler2
            # Should only be called once
            assert mock.call_count == 1


def _create_mock_crawler() -> MagicMock:
    """Create a properly mocked crawler with async methods."""
    crawler = MagicMock()
    crawler.is_available = AsyncMock(return_value=False)  # Disable crawling in tests
    crawler.search = AsyncMock(return_value=[])
    crawler.crawl_search_results = AsyncMock(return_value=[])
    return crawler


class TestCollectNode:
    """Test suite for collect_node function."""

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.collect.get_crawler")
    @patch("research_tool.agent.nodes.collect.SemanticScholarProvider")
    @patch("research_tool.agent.nodes.collect.PubMedProvider")
    @patch("research_tool.agent.nodes.collect.ArxivProvider")
    async def test_collect_returns_state_updates(
        self,
        mock_arxiv: MagicMock,
        mock_pubmed: MagicMock,
        mock_scholar: MagicMock,
        mock_crawler: MagicMock
    ) -> None:
        """collect_node returns dict with state updates."""
        # Setup mocks
        for mock_provider in [mock_arxiv, mock_pubmed, mock_scholar]:
            provider = MagicMock()
            provider.search = AsyncMock(return_value=[])
            provider.is_available = AsyncMock(return_value=True)
            mock_provider.return_value = provider

        mock_crawler.return_value = _create_mock_crawler()

        state = {"original_query": "test query", "domain": "general"}
        result = await collect_node(state)

        assert isinstance(result, dict)
        assert "current_phase" in result
        assert result["current_phase"] == "collect"

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.collect.get_crawler")
    @patch("research_tool.agent.nodes.collect.SemanticScholarProvider")
    @patch("research_tool.agent.nodes.collect.PubMedProvider")
    @patch("research_tool.agent.nodes.collect.ArxivProvider")
    async def test_collect_uses_refined_query(
        self,
        mock_arxiv: MagicMock,
        mock_pubmed: MagicMock,
        mock_scholar: MagicMock,
        mock_crawler: MagicMock
    ) -> None:
        """collect_node uses refined_query when available."""
        provider = MagicMock()
        provider.search = AsyncMock(return_value=[])
        provider.is_available = AsyncMock(return_value=True)

        for mock in [mock_arxiv, mock_pubmed, mock_scholar]:
            mock.return_value = provider

        mock_crawler.return_value = _create_mock_crawler()

        state = {
            "original_query": "original",
            "refined_query": "refined query",
            "domain": "general"
        }
        await collect_node(state)

        # Verify search was called (providers are used)
        assert provider.search.called


class TestCollectDomainConfiguration:
    """Test domain-specific configuration in collect node."""

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.collect.get_crawler")
    @patch("research_tool.agent.nodes.collect.DomainConfiguration")
    @patch("research_tool.agent.nodes.collect.SemanticScholarProvider")
    @patch("research_tool.agent.nodes.collect.PubMedProvider")
    @patch("research_tool.agent.nodes.collect.ArxivProvider")
    async def test_collect_uses_medical_config(
        self,
        mock_arxiv: MagicMock,
        mock_pubmed: MagicMock,
        mock_scholar: MagicMock,
        mock_config: MagicMock,
        mock_crawler: MagicMock
    ) -> None:
        """Uses medical configuration for medical domain."""
        provider = MagicMock()
        provider.search = AsyncMock(return_value=[])
        provider.is_available = AsyncMock(return_value=True)

        for mock in [mock_arxiv, mock_pubmed, mock_scholar]:
            mock.return_value = provider

        mock_config.for_medical.return_value = MagicMock(
            primary_sources=["pubmed", "semantic_scholar"],
            secondary_sources=["arxiv"]
        )
        mock_crawler.return_value = _create_mock_crawler()

        state = {"original_query": "test", "domain": "medical"}
        await collect_node(state)

        mock_config.for_medical.assert_called_once()

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.collect.get_crawler")
    @patch("research_tool.agent.nodes.collect.DomainConfiguration")
    @patch("research_tool.agent.nodes.collect.SemanticScholarProvider")
    @patch("research_tool.agent.nodes.collect.PubMedProvider")
    @patch("research_tool.agent.nodes.collect.ArxivProvider")
    async def test_collect_uses_academic_config(
        self,
        mock_arxiv: MagicMock,
        mock_pubmed: MagicMock,
        mock_scholar: MagicMock,
        mock_config: MagicMock,
        mock_crawler: MagicMock
    ) -> None:
        """Uses academic configuration for academic domain."""
        provider = MagicMock()
        provider.search = AsyncMock(return_value=[])
        provider.is_available = AsyncMock(return_value=True)

        for mock in [mock_arxiv, mock_pubmed, mock_scholar]:
            mock.return_value = provider

        mock_config.for_academic.return_value = MagicMock(
            primary_sources=["semantic_scholar", "arxiv"],
            secondary_sources=[]
        )
        mock_crawler.return_value = _create_mock_crawler()

        state = {"original_query": "test", "domain": "academic"}
        await collect_node(state)

        mock_config.for_academic.assert_called_once()


class TestCollectProviderInitialization:
    """Test provider initialization in collect node."""

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.collect.get_crawler")
    @patch("research_tool.agent.nodes.collect.TavilyProvider")
    @patch("research_tool.agent.nodes.collect.SemanticScholarProvider")
    @patch("research_tool.agent.nodes.collect.PubMedProvider")
    @patch("research_tool.agent.nodes.collect.ArxivProvider")
    async def test_collect_handles_tavily_not_configured(
        self,
        mock_arxiv: MagicMock,
        mock_pubmed: MagicMock,
        mock_scholar: MagicMock,
        mock_tavily: MagicMock,
        mock_crawler: MagicMock
    ) -> None:
        """collect_node handles Tavily not being configured."""
        # Tavily raises ValueError when not configured
        mock_tavily.side_effect = ValueError("TAVILY_API_KEY not configured")

        provider = MagicMock()
        provider.search = AsyncMock(return_value=[])
        provider.is_available = AsyncMock(return_value=True)

        for mock in [mock_arxiv, mock_pubmed, mock_scholar]:
            mock.return_value = provider

        mock_crawler.return_value = _create_mock_crawler()

        state = {"original_query": "test", "domain": "general"}
        # Should not raise
        result = await collect_node(state)
        assert result is not None

    @pytest.mark.asyncio
    @patch("research_tool.agent.nodes.collect.get_crawler")
    @patch("research_tool.agent.nodes.collect.BraveProvider")
    @patch("research_tool.agent.nodes.collect.SemanticScholarProvider")
    @patch("research_tool.agent.nodes.collect.PubMedProvider")
    @patch("research_tool.agent.nodes.collect.ArxivProvider")
    async def test_collect_handles_brave_not_configured(
        self,
        mock_arxiv: MagicMock,
        mock_pubmed: MagicMock,
        mock_scholar: MagicMock,
        mock_brave: MagicMock,
        mock_crawler: MagicMock
    ) -> None:
        """collect_node handles Brave not being configured."""
        # Brave may not have API key
        mock_brave.side_effect = ValueError("BRAVE_API_KEY not configured")

        provider = MagicMock()
        provider.search = AsyncMock(return_value=[])
        provider.is_available = AsyncMock(return_value=True)

        for mock in [mock_arxiv, mock_pubmed, mock_scholar]:
            mock.return_value = provider

        mock_crawler.return_value = _create_mock_crawler()

        state = {"original_query": "test", "domain": "general"}
        # Should not raise
        result = await collect_node(state)
        assert result is not None
