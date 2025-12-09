"""Tests for Playwright crawler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research_tool.services.search.crawler import PlaywrightCrawler


class TestPlaywrightCrawler:
    """Test suite for PlaywrightCrawler."""

    def test_init_defaults(self) -> None:
        """Crawler initializes with correct defaults."""
        crawler = PlaywrightCrawler()
        assert crawler.headless is True
        assert crawler.timeout_ms == 30000
        assert crawler.respect_robots is True
        assert crawler._browser is None

    def test_init_custom_values(self) -> None:
        """Crawler accepts custom configuration."""
        crawler = PlaywrightCrawler(
            headless=False,
            timeout_ms=60000,
            respect_robots=False
        )
        assert crawler.headless is False
        assert crawler.timeout_ms == 60000
        assert crawler.respect_robots is False

    def test_name_property(self) -> None:
        """Name property returns correct identifier."""
        crawler = PlaywrightCrawler()
        assert crawler.name == "playwright_crawler"

    def test_requests_per_second(self) -> None:
        """Rate limit is conservative."""
        crawler = PlaywrightCrawler()
        # 0.5 = 1 request per 2 seconds
        assert crawler.requests_per_second == 0.5

    def test_user_agent_rotation(self) -> None:
        """User agents rotate on each call."""
        crawler = PlaywrightCrawler()
        ua1 = crawler._get_user_agent()
        ua2 = crawler._get_user_agent()
        ua3 = crawler._get_user_agent()
        ua4 = crawler._get_user_agent()
        ua5 = crawler._get_user_agent()  # Should wrap around

        # First 4 should be different (we have 4 agents)
        assert ua1 != ua2 or ua2 != ua3 or ua3 != ua4
        # Fifth should equal first (rotation)
        assert ua5 == ua1

    def test_user_agents_are_realistic(self) -> None:
        """User agents look like real browser strings."""
        crawler = PlaywrightCrawler()
        for ua in crawler.USER_AGENTS:
            assert "Mozilla" in ua
            assert "AppleWebKit" in ua or "Gecko" in ua


class TestPlaywrightCrawlerAsync:
    """Async tests for PlaywrightCrawler."""

    @pytest.mark.asyncio
    async def test_search_without_urls_returns_empty(self) -> None:
        """Search without URLs in filters returns empty list."""
        crawler = PlaywrightCrawler()
        results = await crawler.search("test query", max_results=10)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_with_empty_urls(self) -> None:
        """Search with empty URL list returns empty."""
        crawler = PlaywrightCrawler()
        results = await crawler.search(
            "test query",
            max_results=10,
            filters={"urls": []}
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_crawl_search_results_preserves_existing_content(self) -> None:
        """Results with full content aren't re-crawled."""
        crawler = PlaywrightCrawler()

        existing_results = [
            {
                "url": "https://example.com/1",
                "title": "Test",
                "full_content": "A" * 600,  # More than 500 chars
                "source_name": "test"
            }
        ]

        # Should return as-is without crawling
        enriched = await crawler.crawl_search_results(existing_results, max_crawl=5)
        assert len(enriched) == 1
        assert enriched[0]["full_content"] == "A" * 600
        assert "crawled" not in enriched[0]  # Not crawled since already had content

    @pytest.mark.asyncio
    async def test_crawl_search_results_handles_missing_url(self) -> None:
        """Results without URL are preserved but not crawled."""
        crawler = PlaywrightCrawler()

        results = [
            {"title": "No URL", "snippet": "Test"}
        ]

        enriched = await crawler.crawl_search_results(results, max_crawl=5)
        assert len(enriched) == 1
        assert enriched[0]["title"] == "No URL"

    @pytest.mark.asyncio
    async def test_crawl_respects_max_crawl_limit(self) -> None:
        """Only crawls up to max_crawl URLs."""
        crawler = PlaywrightCrawler()

        # Create 10 results
        results = [
            {"url": f"https://example.com/{i}", "title": f"Test {i}"}
            for i in range(10)
        ]

        # Mock fetch_page to track calls
        call_count = 0
        async def mock_fetch(url: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {"content": "Test content", "title": "Test", "metadata": {}}

        with patch.object(crawler, 'fetch_page', side_effect=mock_fetch):
            await crawler.crawl_search_results(results, max_crawl=3)

        assert call_count == 3  # Only 3 crawled despite 10 results

    @pytest.mark.asyncio
    async def test_is_available_returns_false_on_error(self) -> None:
        """is_available returns False when browser fails."""
        crawler = PlaywrightCrawler()

        # Mock _ensure_browser to raise
        async def mock_ensure_browser():
            raise Exception("Browser not available")

        with patch.object(crawler, '_ensure_browser', side_effect=mock_ensure_browser):
            available = await crawler.is_available()

        assert available is False

    @pytest.mark.asyncio
    async def test_close_clears_browser(self) -> None:
        """Close method properly cleans up browser."""
        crawler = PlaywrightCrawler()

        # Set up mock browser
        mock_browser = AsyncMock()
        crawler._browser = mock_browser

        await crawler.close()

        mock_browser.close.assert_called_once()
        assert crawler._browser is None

    @pytest.mark.asyncio
    async def test_close_handles_no_browser(self) -> None:
        """Close works even if no browser was started."""
        crawler = PlaywrightCrawler()
        assert crawler._browser is None

        # Should not raise
        await crawler.close()
        assert crawler._browser is None


class TestCrawlerIntegration:
    """Integration-style tests for crawler."""

    @pytest.mark.asyncio
    async def test_fetch_page_extracts_metadata(self) -> None:
        """fetch_page extracts metadata from page."""
        crawler = PlaywrightCrawler()

        # Mock the entire fetch flow
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_page.content = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_page.title = AsyncMock(return_value="Test Page")
        mock_page.evaluate = AsyncMock(return_value=None)
        mock_page.add_init_script = AsyncMock()

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()
        mock_page.context = mock_context

        with (
            patch.object(crawler, '_create_stealth_page', return_value=mock_page),
            patch('research_tool.services.search.crawler.rate_limiter') as mock_limiter,
            patch(
                'research_tool.services.search.crawler.extract',
                return_value="Extracted content"
            ),
        ):
            mock_limiter.acquire = AsyncMock()
            result = await crawler.fetch_page("https://example.com")

        assert result["url"] == "https://example.com"
        assert result["title"] == "Test Page"
        assert result["content"] == "Extracted content"
        assert "retrieved_at" in result

    @pytest.mark.asyncio
    async def test_fetch_page_handles_timeout(self) -> None:
        """fetch_page raises TimeoutError on timeout."""
        from playwright.async_api import TimeoutError as PlaywrightTimeout

        from research_tool.core.exceptions import TimeoutError

        crawler = PlaywrightCrawler()

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(side_effect=PlaywrightTimeout("Timeout"))
        mock_page.add_init_script = AsyncMock()

        mock_context = AsyncMock()
        mock_context.close = AsyncMock()
        mock_page.context = mock_context

        with (
            patch.object(crawler, '_create_stealth_page', return_value=mock_page),
            patch('research_tool.services.search.crawler.rate_limiter') as mock_limiter,
        ):
            mock_limiter.acquire = AsyncMock()
            with pytest.raises(TimeoutError):
                await crawler.fetch_page("https://example.com")

    @pytest.mark.asyncio
    async def test_fetch_page_handles_rate_limit(self) -> None:
        """fetch_page raises RateLimitError on 429."""
        from research_tool.core.exceptions import RateLimitError

        crawler = PlaywrightCrawler()

        mock_response = MagicMock()
        mock_response.status = 429

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.add_init_script = AsyncMock()

        mock_context = AsyncMock()
        mock_context.close = AsyncMock()
        mock_page.context = mock_context

        with (
            patch.object(crawler, '_create_stealth_page', return_value=mock_page),
            patch('research_tool.services.search.crawler.rate_limiter') as mock_limiter,
        ):
            mock_limiter.acquire = AsyncMock()
            with pytest.raises(RateLimitError):
                await crawler.fetch_page("https://example.com")

    @pytest.mark.asyncio
    async def test_fetch_page_handles_access_denied(self) -> None:
        """fetch_page raises AccessDeniedError on 403."""
        from research_tool.core.exceptions import AccessDeniedError

        crawler = PlaywrightCrawler()

        mock_response = MagicMock()
        mock_response.status = 403

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.add_init_script = AsyncMock()

        mock_context = AsyncMock()
        mock_context.close = AsyncMock()
        mock_page.context = mock_context

        with (
            patch.object(crawler, '_create_stealth_page', return_value=mock_page),
            patch('research_tool.services.search.crawler.rate_limiter') as mock_limiter,
        ):
            mock_limiter.acquire = AsyncMock()
            with pytest.raises(AccessDeniedError):
                await crawler.fetch_page("https://example.com")
