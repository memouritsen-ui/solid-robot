"""Tests for PubMed search provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from research_tool.services.search.pubmed import PubMedProvider


class TestPubMedProviderProperties:
    """Test PubMedProvider properties."""

    def test_name_property(self) -> None:
        """name returns 'pubmed'."""
        provider = PubMedProvider()
        assert provider.name == "pubmed"

    def test_requests_per_second(self) -> None:
        """requests_per_second returns 3.0."""
        provider = PubMedProvider()
        assert provider.requests_per_second == 3.0

    def test_base_url_is_correct(self) -> None:
        """BASE_URL is set correctly."""
        assert PubMedProvider.BASE_URL == "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class TestPubMedProviderSearch:
    """Test PubMedProvider search functionality."""

    @patch("research_tool.services.search.pubmed.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_returns_results(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search returns standardized results."""
        mock_limiter.acquire = AsyncMock()

        # Mock esearch response
        search_response = MagicMock()
        search_response.json.return_value = {
            "esearchresult": {"idlist": ["12345678"]}
        }
        search_response.raise_for_status = MagicMock()

        # Mock esummary response
        fetch_response = MagicMock()
        fetch_response.json.return_value = {
            "result": {
                "12345678": {
                    "title": "Test Medical Paper",
                    "source": "Test Journal",
                    "authors": [{"name": "Smith J"}],
                    "fulljournalname": "Test Journal of Medicine",
                    "pubdate": "2024 Jan",
                    "pubtype": ["Journal Article"],
                    "elocationid": "doi: 10.1234/test"
                }
            }
        }
        fetch_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(
            side_effect=[search_response, fetch_response]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = PubMedProvider()
        results = await provider.search("cancer treatment", max_results=5)

        assert len(results) == 1
        assert results[0]["url"] == "https://pubmed.ncbi.nlm.nih.gov/12345678/"
        assert results[0]["title"] == "Test Medical Paper"
        assert results[0]["source_name"] == "pubmed"
        assert "Smith J" in results[0]["metadata"]["authors"]

    @patch("research_tool.services.search.pubmed.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_respects_rate_limit(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search calls rate limiter before each API call."""
        mock_limiter.acquire = AsyncMock()

        search_response = MagicMock()
        search_response.json.return_value = {
            "esearchresult": {"idlist": ["12345678"]}
        }
        search_response.raise_for_status = MagicMock()

        fetch_response = MagicMock()
        fetch_response.json.return_value = {
            "result": {
                "12345678": {
                    "title": "Test",
                    "source": "Test",
                    "authors": []
                }
            }
        }
        fetch_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(
            side_effect=[search_response, fetch_response]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = PubMedProvider()
        await provider.search("test")

        # Should be called twice - once for search, once for fetch
        assert mock_limiter.acquire.call_count == 2

    @patch("research_tool.services.search.pubmed.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_returns_empty_on_no_results(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search returns empty list when no PMIDs found."""
        mock_limiter.acquire = AsyncMock()

        search_response = MagicMock()
        search_response.json.return_value = {
            "esearchresult": {"idlist": []}
        }
        search_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=search_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = PubMedProvider()
        results = await provider.search("nonexistent query xyz123")

        assert results == []

    @patch("research_tool.services.search.pubmed.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_handles_search_http_error(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search returns empty list on esearch HTTP error."""
        mock_limiter.acquire = AsyncMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPError("Connection failed")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = PubMedProvider()
        results = await provider.search("test")

        assert results == []

    @patch("research_tool.services.search.pubmed.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_handles_fetch_http_error(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search returns empty list on esummary HTTP error."""
        mock_limiter.acquire = AsyncMock()

        search_response = MagicMock()
        search_response.json.return_value = {
            "esearchresult": {"idlist": ["12345678"]}
        }
        search_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        call_count = [0]

        async def mock_get(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return search_response
            raise httpx.HTTPError("Fetch failed")

        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = PubMedProvider()
        results = await provider.search("test")

        assert results == []

    @patch("research_tool.services.search.pubmed.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_skips_missing_articles(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search skips PMIDs not in fetch response."""
        mock_limiter.acquire = AsyncMock()

        search_response = MagicMock()
        search_response.json.return_value = {
            "esearchresult": {"idlist": ["12345678", "99999999"]}
        }
        search_response.raise_for_status = MagicMock()

        fetch_response = MagicMock()
        fetch_response.json.return_value = {
            "result": {
                "12345678": {
                    "title": "Found Article",
                    "source": "Test",
                    "authors": []
                }
                # 99999999 is missing
            }
        }
        fetch_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(
            side_effect=[search_response, fetch_response]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = PubMedProvider()
        results = await provider.search("test")

        assert len(results) == 1
        assert results[0]["title"] == "Found Article"


class TestPubMedProviderAvailability:
    """Test PubMedProvider availability check."""

    @pytest.mark.asyncio
    async def test_is_available_returns_true(self) -> None:
        """is_available always returns True (no API key needed)."""
        provider = PubMedProvider()
        assert await provider.is_available() is True
