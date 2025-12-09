"""Tests for arXiv search provider."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research_tool.services.search.arxiv import ArxivProvider


class TestArxivProviderProperties:
    """Test ArxivProvider properties."""

    def test_name_property(self) -> None:
        """name returns 'arxiv'."""
        with patch("research_tool.services.search.arxiv.arxiv"):
            provider = ArxivProvider()
            assert provider.name == "arxiv"

    def test_requests_per_second(self) -> None:
        """requests_per_second returns 1.0."""
        with patch("research_tool.services.search.arxiv.arxiv"):
            provider = ArxivProvider()
            assert provider.requests_per_second == 1.0


class TestArxivProviderInit:
    """Test ArxivProvider initialization."""

    @patch("research_tool.services.search.arxiv.arxiv")
    def test_init_creates_client(self, mock_arxiv: MagicMock) -> None:
        """Provider creates arxiv client on init."""
        provider = ArxivProvider()
        mock_arxiv.Client.assert_called_once()
        assert provider.client is not None


class TestArxivProviderSearch:
    """Test ArxivProvider search functionality."""

    @patch("research_tool.services.search.arxiv.rate_limiter")
    @patch("research_tool.services.search.arxiv.arxiv")
    @pytest.mark.asyncio
    async def test_search_returns_results(
        self, mock_arxiv: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search returns standardized results."""
        mock_limiter.acquire = AsyncMock()

        # Create mock result
        mock_result = MagicMock()
        mock_result.entry_id = "https://arxiv.org/abs/2401.00001"
        mock_result.title = "Test Paper"
        mock_result.summary = "This is a test abstract"
        mock_result.authors = [MagicMock(name="Author One")]
        mock_result.authors[0].name = "Author One"
        mock_result.published = datetime(2024, 1, 1)
        mock_result.updated = datetime(2024, 1, 2)
        mock_result.categories = ["cs.AI", "cs.LG"]
        mock_result.primary_category = "cs.AI"
        mock_result.doi = "10.1234/test"
        mock_result.pdf_url = "https://arxiv.org/pdf/2401.00001"
        mock_result.comment = "Accepted at TestConf 2024"

        mock_client = MagicMock()
        mock_client.results.return_value = [mock_result]
        mock_arxiv.Client.return_value = mock_client
        mock_arxiv.Search.return_value = MagicMock()
        mock_arxiv.SortCriterion.Relevance = "relevance"

        provider = ArxivProvider()
        results = await provider.search("machine learning", max_results=5)

        assert len(results) == 1
        assert results[0]["url"] == "https://arxiv.org/abs/2401.00001"
        assert results[0]["title"] == "Test Paper"
        assert results[0]["source_name"] == "arxiv"
        assert "Author One" in results[0]["metadata"]["authors"]
        assert results[0]["metadata"]["primary_category"] == "cs.AI"

    @patch("research_tool.services.search.arxiv.rate_limiter")
    @patch("research_tool.services.search.arxiv.arxiv")
    @pytest.mark.asyncio
    async def test_search_respects_rate_limit(
        self, mock_arxiv: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search calls rate limiter before API call."""
        mock_limiter.acquire = AsyncMock()
        mock_client = MagicMock()
        mock_client.results.return_value = []
        mock_arxiv.Client.return_value = mock_client
        mock_arxiv.Search.return_value = MagicMock()
        mock_arxiv.SortCriterion.Relevance = "relevance"

        provider = ArxivProvider()
        await provider.search("test")

        mock_limiter.acquire.assert_called_once_with("arxiv", 1.0)

    @patch("research_tool.services.search.arxiv.rate_limiter")
    @patch("research_tool.services.search.arxiv.arxiv")
    @pytest.mark.asyncio
    async def test_search_handles_exception(
        self, mock_arxiv: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search returns empty list on exception."""
        mock_limiter.acquire = AsyncMock()
        mock_client = MagicMock()
        mock_client.results.side_effect = Exception("API error")
        mock_arxiv.Client.return_value = mock_client
        mock_arxiv.Search.return_value = MagicMock()
        mock_arxiv.SortCriterion.Relevance = "relevance"

        provider = ArxivProvider()
        results = await provider.search("test")

        assert results == []

    @patch("research_tool.services.search.arxiv.rate_limiter")
    @patch("research_tool.services.search.arxiv.arxiv")
    @pytest.mark.asyncio
    async def test_search_truncates_long_snippets(
        self, mock_arxiv: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search truncates summaries longer than 500 chars for snippet."""
        mock_limiter.acquire = AsyncMock()

        long_summary = "A" * 1000
        mock_result = MagicMock()
        mock_result.entry_id = "https://arxiv.org/abs/2401.00001"
        mock_result.title = "Test"
        mock_result.summary = long_summary
        mock_result.authors = []
        mock_result.published = None
        mock_result.updated = None
        mock_result.categories = []
        mock_result.primary_category = None
        mock_result.doi = None
        mock_result.pdf_url = None
        mock_result.comment = None

        mock_client = MagicMock()
        mock_client.results.return_value = [mock_result]
        mock_arxiv.Client.return_value = mock_client
        mock_arxiv.Search.return_value = MagicMock()
        mock_arxiv.SortCriterion.Relevance = "relevance"

        provider = ArxivProvider()
        results = await provider.search("test")

        assert len(results[0]["snippet"]) == 500
        assert results[0]["full_content"] == long_summary  # Full version preserved


class TestArxivProviderAvailability:
    """Test ArxivProvider availability check."""

    @patch("research_tool.services.search.arxiv.arxiv")
    @pytest.mark.asyncio
    async def test_is_available_returns_true(self, mock_arxiv: MagicMock) -> None:
        """is_available always returns True (no API key needed)."""
        provider = ArxivProvider()
        assert await provider.is_available() is True
