"""Tests for Semantic Scholar search provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from research_tool.services.search.semantic_scholar import SemanticScholarProvider


class TestSemanticScholarProviderProperties:
    """Test SemanticScholarProvider properties."""

    def test_name_property(self) -> None:
        """name returns 'semantic_scholar'."""
        provider = SemanticScholarProvider()
        assert provider.name == "semantic_scholar"

    def test_requests_per_second_is_strict(self) -> None:
        """requests_per_second is 1.0 (strict limit)."""
        provider = SemanticScholarProvider()
        assert provider.requests_per_second == 1.0

    def test_base_url_is_correct(self) -> None:
        """BASE_URL is set correctly."""
        assert SemanticScholarProvider.BASE_URL == "https://api.semanticscholar.org/graph/v1"


class TestSemanticScholarProviderSearch:
    """Test SemanticScholarProvider search functionality."""

    @patch("research_tool.services.search.semantic_scholar.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_returns_results(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search returns standardized results."""
        mock_limiter.acquire = AsyncMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "paperId": "abc123",
                    "title": "Deep Learning for NLP",
                    "abstract": "This paper presents...",
                    "authors": [{"name": "John Smith"}],
                    "year": 2024,
                    "citationCount": 100,
                    "venue": "NeurIPS",
                    "publicationTypes": ["Conference"]
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = SemanticScholarProvider()
        results = await provider.search("deep learning", max_results=5)

        assert len(results) == 1
        assert "abc123" in results[0]["url"]
        assert results[0]["title"] == "Deep Learning for NLP"
        assert results[0]["snippet"] == "This paper presents..."
        assert results[0]["source_name"] == "semantic_scholar"
        assert results[0]["metadata"]["citations"] == 100
        assert "John Smith" in results[0]["metadata"]["authors"]

    @patch("research_tool.services.search.semantic_scholar.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_respects_strict_rate_limit(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search calls rate limiter with strict 1.0 RPS."""
        mock_limiter.acquire = AsyncMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = SemanticScholarProvider()
        await provider.search("test")

        # Must be called with exactly 1.0 RPS
        mock_limiter.acquire.assert_called_once_with("semantic_scholar", 1.0)

    @patch("research_tool.services.search.semantic_scholar.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_with_filters(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search passes filters to API."""
        mock_limiter.acquire = AsyncMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = SemanticScholarProvider()
        await provider.search(
            "test",
            filters={"year": "2024", "fieldsOfStudy": "Computer Science"}
        )

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["year"] == "2024"
        assert call_kwargs["params"]["fieldsOfStudy"] == "Computer Science"

    @patch("research_tool.services.search.semantic_scholar.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_caps_max_results_at_100(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search caps max_results at API limit of 100."""
        mock_limiter.acquire = AsyncMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = SemanticScholarProvider()
        await provider.search("test", max_results=500)

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["limit"] == 100  # Capped

    @patch("research_tool.services.search.semantic_scholar.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_handles_http_error(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search returns empty list on HTTP error."""
        mock_limiter.acquire = AsyncMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPError("Rate limited")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = SemanticScholarProvider()
        results = await provider.search("test")

        assert results == []

    @patch("research_tool.services.search.semantic_scholar.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_skips_papers_without_id(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search skips papers missing paperId."""
        mock_limiter.acquire = AsyncMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"title": "No ID Paper", "abstract": "Test"},  # Missing paperId
                {
                    "paperId": "abc123",
                    "title": "Valid Paper",
                    "abstract": "Test",
                    "authors": [],
                    "year": 2024
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = SemanticScholarProvider()
        results = await provider.search("test")

        assert len(results) == 1
        assert results[0]["title"] == "Valid Paper"

    @patch("research_tool.services.search.semantic_scholar.rate_limiter")
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_search_requests_correct_fields(
        self, mock_client_class: MagicMock, mock_limiter: MagicMock
    ) -> None:
        """search requests all needed fields from API."""
        mock_limiter.acquire = AsyncMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = SemanticScholarProvider()
        await provider.search("test")

        call_kwargs = mock_client.get.call_args[1]
        fields = call_kwargs["params"]["fields"]
        assert "title" in fields
        assert "abstract" in fields
        assert "authors" in fields
        assert "citationCount" in fields


class TestSemanticScholarProviderAvailability:
    """Test SemanticScholarProvider availability check."""

    @pytest.mark.asyncio
    async def test_is_available_returns_true(self) -> None:
        """is_available returns True (no API key for basic access)."""
        provider = SemanticScholarProvider()
        assert await provider.is_available() is True
