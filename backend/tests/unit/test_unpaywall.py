"""Tests for Unpaywall open access finder."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research_tool.services.search.unpaywall import UnpaywallProvider


class TestUnpaywallProviderInit:
    """Test UnpaywallProvider initialization."""

    @patch("research_tool.services.search.unpaywall.settings")
    def test_init_with_email(self, mock_settings: MagicMock) -> None:
        """Provider initializes when email is configured."""
        mock_settings.unpaywall_email = "test@example.com"

        provider = UnpaywallProvider()
        assert provider is not None

    @patch("research_tool.services.search.unpaywall.settings")
    def test_init_without_email_raises(self, mock_settings: MagicMock) -> None:
        """Provider raises ValueError when email missing."""
        mock_settings.unpaywall_email = None

        with pytest.raises(ValueError, match="UNPAYWALL_EMAIL not configured"):
            UnpaywallProvider()


class TestUnpaywallProviderProperties:
    """Test UnpaywallProvider properties."""

    @patch("research_tool.services.search.unpaywall.settings")
    def test_name_property(self, mock_settings: MagicMock) -> None:
        """name returns 'unpaywall'."""
        mock_settings.unpaywall_email = "test@example.com"
        provider = UnpaywallProvider()
        assert provider.name == "unpaywall"

    @patch("research_tool.services.search.unpaywall.settings")
    def test_requests_per_second(self, mock_settings: MagicMock) -> None:
        """requests_per_second returns 10.0 (100k/day limit)."""
        mock_settings.unpaywall_email = "test@example.com"
        provider = UnpaywallProvider()
        assert provider.requests_per_second == 10.0


class TestUnpaywallProviderGetOpenAccess:
    """Test UnpaywallProvider get_open_access functionality."""

    @patch("research_tool.services.search.unpaywall.settings")
    @patch("research_tool.services.search.unpaywall.rate_limiter")
    @pytest.mark.asyncio
    async def test_get_open_access_returns_result(
        self,
        mock_limiter: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """get_open_access returns OA location for valid DOI."""
        mock_settings.unpaywall_email = "test@example.com"
        mock_limiter.acquire = AsyncMock()

        provider = UnpaywallProvider()

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "doi": "10.1234/test",
            "title": "Test Paper",
            "is_oa": True,
            "best_oa_location": {
                "url": "https://example.com/paper.pdf",
                "url_for_pdf": "https://example.com/paper.pdf",
                "license": "cc-by",
                "version": "publishedVersion",
                "host_type": "repository"
            },
            "oa_locations": [
                {
                    "url": "https://example.com/paper.pdf",
                    "url_for_pdf": "https://example.com/paper.pdf"
                }
            ]
        }

        with patch("research_tool.services.search.unpaywall.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await provider.get_open_access("10.1234/test")

        assert result is not None
        assert result["doi"] == "10.1234/test"
        assert result["is_oa"] is True
        assert result["best_oa_url"] == "https://example.com/paper.pdf"

    @patch("research_tool.services.search.unpaywall.settings")
    @patch("research_tool.services.search.unpaywall.rate_limiter")
    @pytest.mark.asyncio
    async def test_get_open_access_not_found(
        self,
        mock_limiter: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """get_open_access returns None for non-OA DOI."""
        mock_settings.unpaywall_email = "test@example.com"
        mock_limiter.acquire = AsyncMock()

        provider = UnpaywallProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "doi": "10.1234/closed",
            "title": "Closed Paper",
            "is_oa": False,
            "best_oa_location": None,
            "oa_locations": []
        }

        with patch("research_tool.services.search.unpaywall.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await provider.get_open_access("10.1234/closed")

        assert result is not None
        assert result["is_oa"] is False
        assert result["best_oa_url"] is None

    @patch("research_tool.services.search.unpaywall.settings")
    @patch("research_tool.services.search.unpaywall.rate_limiter")
    @pytest.mark.asyncio
    async def test_get_open_access_invalid_doi(
        self,
        mock_limiter: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """get_open_access returns None for invalid DOI."""
        mock_settings.unpaywall_email = "test@example.com"
        mock_limiter.acquire = AsyncMock()

        provider = UnpaywallProvider()

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("research_tool.services.search.unpaywall.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await provider.get_open_access("invalid-doi")

        assert result is None

    @patch("research_tool.services.search.unpaywall.settings")
    @patch("research_tool.services.search.unpaywall.rate_limiter")
    @pytest.mark.asyncio
    async def test_get_open_access_respects_rate_limit(
        self,
        mock_limiter: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """get_open_access calls rate limiter before API call."""
        mock_settings.unpaywall_email = "test@example.com"
        mock_limiter.acquire = AsyncMock()

        provider = UnpaywallProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"is_oa": False, "best_oa_location": None}

        with patch("research_tool.services.search.unpaywall.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            await provider.get_open_access("10.1234/test")

        mock_limiter.acquire.assert_called_once_with("unpaywall", 10.0)


class TestUnpaywallProviderSearch:
    """Test UnpaywallProvider search functionality (batch DOI lookup)."""

    @patch("research_tool.services.search.unpaywall.settings")
    @patch("research_tool.services.search.unpaywall.rate_limiter")
    @pytest.mark.asyncio
    async def test_search_with_dois_filter(
        self,
        mock_limiter: MagicMock,
        mock_settings: MagicMock
    ) -> None:
        """search returns OA results for DOIs in filter."""
        mock_settings.unpaywall_email = "test@example.com"
        mock_limiter.acquire = AsyncMock()

        provider = UnpaywallProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "doi": "10.1234/test",
            "title": "Test Paper",
            "is_oa": True,
            "best_oa_location": {
                "url": "https://example.com/paper.pdf",
                "url_for_pdf": "https://example.com/paper.pdf"
            }
        }

        with patch("research_tool.services.search.unpaywall.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            results = await provider.search(
                query="",
                filters={"dois": ["10.1234/test"]}
            )

        assert len(results) == 1
        assert results[0]["url"] == "https://example.com/paper.pdf"
        assert results[0]["source_name"] == "unpaywall"

    @patch("research_tool.services.search.unpaywall.settings")
    @pytest.mark.asyncio
    async def test_search_without_dois_returns_empty(
        self,
        mock_settings: MagicMock
    ) -> None:
        """search returns empty when no DOIs provided."""
        mock_settings.unpaywall_email = "test@example.com"

        provider = UnpaywallProvider()
        results = await provider.search("some query")

        assert results == []


class TestUnpaywallProviderAvailability:
    """Test UnpaywallProvider availability check."""

    @patch("research_tool.services.search.unpaywall.settings")
    @pytest.mark.asyncio
    async def test_is_available_with_email(
        self, mock_settings: MagicMock
    ) -> None:
        """is_available returns True when email configured."""
        mock_settings.unpaywall_email = "test@example.com"
        provider = UnpaywallProvider()

        assert await provider.is_available() is True

    @patch("research_tool.services.search.unpaywall.settings")
    @pytest.mark.asyncio
    async def test_is_available_without_email(
        self, mock_settings: MagicMock
    ) -> None:
        """is_available returns False when email missing."""
        mock_settings.unpaywall_email = "test@example.com"
        provider = UnpaywallProvider()

        mock_settings.unpaywall_email = None
        assert await provider.is_available() is False
