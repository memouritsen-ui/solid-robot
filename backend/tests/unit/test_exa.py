"""Tests for Exa search provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research_tool.services.search.exa import ExaProvider


class TestExaProviderInit:
    """Test ExaProvider initialization."""

    @patch("research_tool.services.search.exa.settings")
    def test_init_with_api_key(self, mock_settings: MagicMock) -> None:
        """Provider initializes when API key is configured."""
        mock_settings.exa_api_key = "test-api-key"

        with patch("research_tool.services.search.exa.Exa"):
            provider = ExaProvider()
            assert provider is not None

    @patch("research_tool.services.search.exa.settings")
    def test_init_without_api_key_raises(self, mock_settings: MagicMock) -> None:
        """Provider raises ValueError when API key missing."""
        mock_settings.exa_api_key = None

        with pytest.raises(ValueError, match="EXA_API_KEY not configured"):
            ExaProvider()


class TestExaProviderProperties:
    """Test ExaProvider properties."""

    @patch("research_tool.services.search.exa.settings")
    @patch("research_tool.services.search.exa.Exa")
    def test_name_property(
        self, mock_client: MagicMock, mock_settings: MagicMock
    ) -> None:
        """name returns 'exa'."""
        mock_settings.exa_api_key = "test-key"
        provider = ExaProvider()
        assert provider.name == "exa"

    @patch("research_tool.services.search.exa.settings")
    @patch("research_tool.services.search.exa.Exa")
    def test_requests_per_second(
        self, mock_client: MagicMock, mock_settings: MagicMock
    ) -> None:
        """requests_per_second returns 1.0 (conservative limit)."""
        mock_settings.exa_api_key = "test-key"
        provider = ExaProvider()
        assert provider.requests_per_second == 1.0


class TestExaProviderSearch:
    """Test ExaProvider search functionality."""

    @patch("research_tool.services.search.exa.settings")
    @patch("research_tool.services.search.exa.Exa")
    @patch("research_tool.services.search.exa.rate_limiter")
    @pytest.mark.asyncio
    async def test_search_returns_results(
        self,
        mock_limiter: MagicMock,
        mock_client_class: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search returns standardized results."""
        mock_settings.exa_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        # Mock Exa search_and_contents response
        mock_result = MagicMock()
        mock_result.url = "https://example.com/1"
        mock_result.title = "Test Result"
        mock_result.text = "Full test content from Exa"
        mock_result.published_date = "2024-01-01"
        mock_result.author = "Test Author"
        mock_result.score = 0.92

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_client = MagicMock()
        mock_client.search_and_contents.return_value = mock_response
        mock_client_class.return_value = mock_client

        provider = ExaProvider()
        results = await provider.search("test query", max_results=5)

        assert len(results) == 1
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["title"] == "Test Result"
        assert results[0]["source_name"] == "exa"
        assert results[0]["full_content"] == "Full test content from Exa"
        assert "retrieved_at" in results[0]
        assert results[0]["metadata"]["score"] == 0.92
        assert results[0]["metadata"]["author"] == "Test Author"

    @patch("research_tool.services.search.exa.settings")
    @patch("research_tool.services.search.exa.Exa")
    @patch("research_tool.services.search.exa.rate_limiter")
    @pytest.mark.asyncio
    async def test_search_respects_rate_limit(
        self,
        mock_limiter: MagicMock,
        mock_client_class: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search calls rate limiter before API call."""
        mock_settings.exa_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        mock_response = MagicMock()
        mock_response.results = []

        mock_client = MagicMock()
        mock_client.search_and_contents.return_value = mock_response
        mock_client_class.return_value = mock_client

        provider = ExaProvider()
        await provider.search("test")

        mock_limiter.acquire.assert_called_once_with("exa", 1.0)

    @patch("research_tool.services.search.exa.settings")
    @patch("research_tool.services.search.exa.Exa")
    @patch("research_tool.services.search.exa.rate_limiter")
    @pytest.mark.asyncio
    async def test_search_uses_neural_type(
        self,
        mock_limiter: MagicMock,
        mock_client_class: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search uses neural search type for best results."""
        mock_settings.exa_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        mock_response = MagicMock()
        mock_response.results = []

        mock_client = MagicMock()
        mock_client.search_and_contents.return_value = mock_response
        mock_client_class.return_value = mock_client

        provider = ExaProvider()
        await provider.search("test", max_results=10)

        mock_client.search_and_contents.assert_called_once()
        call_kwargs = mock_client.search_and_contents.call_args[1]
        assert call_kwargs["type"] == "neural"
        assert call_kwargs["text"] is True
        assert call_kwargs["num_results"] == 10

    @patch("research_tool.services.search.exa.settings")
    @patch("research_tool.services.search.exa.Exa")
    @patch("research_tool.services.search.exa.rate_limiter")
    @pytest.mark.asyncio
    async def test_search_handles_empty_results(
        self,
        mock_limiter: MagicMock,
        mock_client_class: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search handles empty results gracefully."""
        mock_settings.exa_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        mock_response = MagicMock()
        mock_response.results = []

        mock_client = MagicMock()
        mock_client.search_and_contents.return_value = mock_response
        mock_client_class.return_value = mock_client

        provider = ExaProvider()
        results = await provider.search("obscure query")

        assert results == []

    @patch("research_tool.services.search.exa.settings")
    @patch("research_tool.services.search.exa.Exa")
    @patch("research_tool.services.search.exa.rate_limiter")
    @pytest.mark.asyncio
    async def test_search_handles_missing_optional_fields(
        self,
        mock_limiter: MagicMock,
        mock_client_class: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search handles results with missing optional fields."""
        mock_settings.exa_api_key = "test-key"
        mock_limiter.acquire = AsyncMock()

        mock_result = MagicMock()
        mock_result.url = "https://example.com/1"
        mock_result.title = "Test Result"
        mock_result.text = None
        mock_result.published_date = None
        mock_result.author = None
        mock_result.score = None

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_client = MagicMock()
        mock_client.search_and_contents.return_value = mock_response
        mock_client_class.return_value = mock_client

        provider = ExaProvider()
        results = await provider.search("test")

        assert len(results) == 1
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["full_content"] is None
        assert results[0]["metadata"]["author"] is None


class TestExaProviderAvailability:
    """Test ExaProvider availability check."""

    @patch("research_tool.services.search.exa.settings")
    @patch("research_tool.services.search.exa.Exa")
    @pytest.mark.asyncio
    async def test_is_available_with_api_key(
        self, mock_client: MagicMock, mock_settings: MagicMock
    ) -> None:
        """is_available returns True when API key configured."""
        mock_settings.exa_api_key = "test-key"
        provider = ExaProvider()

        assert await provider.is_available() is True

    @patch("research_tool.services.search.exa.settings")
    @patch("research_tool.services.search.exa.Exa")
    @pytest.mark.asyncio
    async def test_is_available_without_api_key(
        self, mock_client: MagicMock, mock_settings: MagicMock
    ) -> None:
        """is_available returns False when API key missing."""
        mock_settings.exa_api_key = "test-key"
        provider = ExaProvider()

        mock_settings.exa_api_key = None
        assert await provider.is_available() is False
