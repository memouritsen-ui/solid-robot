"""Tests for Brave search provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from research_tool.services.search.brave import BraveProvider


class TestBraveProviderProperties:
    """Test BraveProvider properties."""

    def test_name_property(self) -> None:
        """name returns 'brave'."""
        provider = BraveProvider()
        assert provider.name == "brave"

    def test_requests_per_second(self) -> None:
        """requests_per_second returns 1.0."""
        provider = BraveProvider()
        assert provider.requests_per_second == 1.0

    def test_base_url_is_correct(self) -> None:
        """BASE_URL is set correctly."""
        assert BraveProvider.BASE_URL == "https://api.search.brave.com/res/v1"


class TestBraveProviderSearch:
    """Test BraveProvider search functionality."""

    @patch("research_tool.services.search.brave.settings")
    @patch("research_tool.services.search.brave.rate_limiter")
    @pytest.mark.asyncio
    async def test_search_returns_empty_without_api_key(
        self, mock_limiter: MagicMock, mock_settings: MagicMock
    ) -> None:
        """search returns empty list when API key not configured."""
        mock_settings.brave_api_key = None

        provider = BraveProvider()
        results = await provider.search("test query")

        assert results == []

    @patch("research_tool.services.search.brave.settings")
    @patch("research_tool.services.search.brave.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_returns_results(
        self,
        mock_client_class: MagicMock,
        mock_limiter: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search returns standardized results."""
        mock_settings.brave_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "url": "https://example.com/1",
                        "title": "Test Result",
                        "description": "Test description",
                        "age": "2 days ago",
                        "language": "en",
                        "family_friendly": True
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = BraveProvider()
        results = await provider.search("test query", max_results=5)

        assert len(results) == 1
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["title"] == "Test Result"
        assert results[0]["snippet"] == "Test description"
        assert results[0]["source_name"] == "brave"
        assert "retrieved_at" in results[0]

    @patch("research_tool.services.search.brave.settings")
    @patch("research_tool.services.search.brave.rate_limiter")
    @pytest.mark.asyncio
    async def test_search_respects_rate_limit(
        self, mock_limiter: MagicMock, mock_settings: MagicMock
    ) -> None:
        """search calls rate limiter before API call."""
        mock_settings.brave_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {"web": {"results": []}}
            mock_response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            provider = BraveProvider()
            await provider.search("test")

        mock_limiter.acquire.assert_called_once_with("brave", 1.0)

    @patch("research_tool.services.search.brave.settings")
    @patch("research_tool.services.search.brave.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_with_filters(
        self,
        mock_client_class: MagicMock,
        mock_limiter: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search passes filters to API."""
        mock_settings.brave_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = BraveProvider()
        await provider.search(
            "test",
            filters={"country": "US", "freshness": "pd"}
        )

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["country"] == "US"
        assert call_kwargs["params"]["freshness"] == "pd"

    @patch("research_tool.services.search.brave.settings")
    @patch("research_tool.services.search.brave.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_handles_http_error(
        self,
        mock_client_class: MagicMock,
        mock_limiter: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search returns empty list on HTTP error."""
        mock_settings.brave_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPError("Connection failed")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = BraveProvider()
        results = await provider.search("test")

        assert results == []

    @patch("research_tool.services.search.brave.settings")
    @patch("research_tool.services.search.brave.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_respects_max_results_cap(
        self,
        mock_client_class: MagicMock,
        mock_limiter: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search caps max_results at API limit of 20."""
        mock_settings.brave_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = BraveProvider()
        await provider.search("test", max_results=100)

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["count"] == 20  # Capped at 20


class TestBraveProviderAvailability:
    """Test BraveProvider availability check."""

    @patch("research_tool.services.search.brave.settings")
    @pytest.mark.asyncio
    async def test_is_available_with_api_key(
        self, mock_settings: MagicMock
    ) -> None:
        """is_available returns True when API key configured."""
        mock_settings.brave_api_key = "test-key"
        provider = BraveProvider()

        assert await provider.is_available() is True

    @patch("research_tool.services.search.brave.settings")
    @pytest.mark.asyncio
    async def test_is_available_without_api_key(
        self, mock_settings: MagicMock
    ) -> None:
        """is_available returns False when API key missing."""
        mock_settings.brave_api_key = None
        provider = BraveProvider()

        assert await provider.is_available() is False
