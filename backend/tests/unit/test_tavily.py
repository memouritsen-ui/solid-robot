"""Tests for Tavily search provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research_tool.services.search.tavily import TavilyProvider


class TestTavilyProviderInit:
    """Test TavilyProvider initialization."""

    @patch("research_tool.services.search.tavily.settings")
    def test_init_with_api_key(self, mock_settings: MagicMock) -> None:
        """Provider initializes when API key is configured."""
        mock_settings.tavily_api_key = "test-api-key"

        with patch("research_tool.services.search.tavily.TavilyClient"):
            provider = TavilyProvider()
            assert provider is not None

    @patch("research_tool.services.search.tavily.settings")
    def test_init_without_api_key_raises(self, mock_settings: MagicMock) -> None:
        """Provider raises ValueError when API key missing."""
        mock_settings.tavily_api_key = None

        with pytest.raises(ValueError, match="TAVILY_API_KEY not configured"):
            TavilyProvider()


class TestTavilyProviderProperties:
    """Test TavilyProvider properties."""

    @patch("research_tool.services.search.tavily.settings")
    @patch("research_tool.services.search.tavily.TavilyClient")
    def test_name_property(
        self, mock_client: MagicMock, mock_settings: MagicMock
    ) -> None:
        """name returns 'tavily'."""
        mock_settings.tavily_api_key = "test-key"
        provider = TavilyProvider()
        assert provider.name == "tavily"

    @patch("research_tool.services.search.tavily.settings")
    @patch("research_tool.services.search.tavily.TavilyClient")
    def test_requests_per_second(
        self, mock_client: MagicMock, mock_settings: MagicMock
    ) -> None:
        """requests_per_second returns 5.0."""
        mock_settings.tavily_api_key = "test-key"
        provider = TavilyProvider()
        assert provider.requests_per_second == 5.0


class TestTavilyProviderSearch:
    """Test TavilyProvider search functionality."""

    @patch("research_tool.services.search.tavily.settings")
    @patch("research_tool.services.search.tavily.TavilyClient")
    @patch("research_tool.services.search.tavily.rate_limiter")
    @pytest.mark.asyncio
    async def test_search_returns_results(
        self,
        mock_limiter: MagicMock,
        mock_client_class: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search returns standardized results."""
        mock_settings.tavily_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [
                {
                    "url": "https://example.com/1",
                    "title": "Test Result",
                    "content": "Test snippet",
                    "raw_content": "Full test content",
                    "score": 0.95,
                    "published_date": "2024-01-01"
                }
            ]
        }
        mock_client_class.return_value = mock_client

        provider = TavilyProvider()
        results = await provider.search("test query", max_results=5)

        assert len(results) == 1
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["title"] == "Test Result"
        assert results[0]["snippet"] == "Test snippet"
        assert results[0]["source_name"] == "tavily"
        assert results[0]["full_content"] == "Full test content"
        assert "retrieved_at" in results[0]
        assert results[0]["metadata"]["score"] == 0.95

    @patch("research_tool.services.search.tavily.settings")
    @patch("research_tool.services.search.tavily.TavilyClient")
    @patch("research_tool.services.search.tavily.rate_limiter")
    @pytest.mark.asyncio
    async def test_search_respects_rate_limit(
        self,
        mock_limiter: MagicMock,
        mock_client_class: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search calls rate limiter before API call."""
        mock_settings.tavily_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        mock_client = MagicMock()
        mock_client.search.return_value = {"results": []}
        mock_client_class.return_value = mock_client

        provider = TavilyProvider()
        await provider.search("test")

        mock_limiter.acquire.assert_called_once_with("tavily", 5.0)

    @patch("research_tool.services.search.tavily.settings")
    @patch("research_tool.services.search.tavily.TavilyClient")
    @patch("research_tool.services.search.tavily.rate_limiter")
    @pytest.mark.asyncio
    async def test_search_uses_advanced_depth(
        self,
        mock_limiter: MagicMock,
        mock_client_class: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search uses advanced search depth."""
        mock_settings.tavily_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        mock_client = MagicMock()
        mock_client.search.return_value = {"results": []}
        mock_client_class.return_value = mock_client

        provider = TavilyProvider()
        await provider.search("test", max_results=10)

        mock_client.search.assert_called_once()
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["search_depth"] == "advanced"
        assert call_kwargs["include_raw_content"] is True


class TestTavilyProviderAvailability:
    """Test TavilyProvider availability check."""

    @patch("research_tool.services.search.tavily.settings")
    @patch("research_tool.services.search.tavily.TavilyClient")
    @pytest.mark.asyncio
    async def test_is_available_with_api_key(
        self, mock_client: MagicMock, mock_settings: MagicMock
    ) -> None:
        """is_available returns True when API key configured."""
        mock_settings.tavily_api_key = "test-key"
        provider = TavilyProvider()

        assert await provider.is_available() is True

    @patch("research_tool.services.search.tavily.settings")
    @patch("research_tool.services.search.tavily.TavilyClient")
    @pytest.mark.asyncio
    async def test_is_available_without_api_key(
        self, mock_client: MagicMock, mock_settings: MagicMock
    ) -> None:
        """is_available returns False when API key missing."""
        # Initialize with key, then remove it
        mock_settings.tavily_api_key = "test-key"
        provider = TavilyProvider()

        mock_settings.tavily_api_key = None
        assert await provider.is_available() is False
