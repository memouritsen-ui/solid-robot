"""Playwright-based web crawler with stealth capabilities.

This module provides a search provider that can:
1. Scrape arbitrary web pages using Playwright
2. Use stealth mode to avoid bot detection
3. Extract clean content using trafilatura
4. Handle obstacles (rate limits, timeouts, access denied)
"""

import asyncio
from contextlib import suppress
from datetime import datetime
from typing import Any

from playwright.async_api import (
    Browser,
    Page,
    async_playwright,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeout,
)
from trafilatura import extract
from trafilatura.settings import use_config

from research_tool.core.config import Settings
from research_tool.core.exceptions import (
    AccessDeniedError,
    RateLimitError,
    TimeoutError,
)
from research_tool.core.logging import get_logger
from research_tool.services.proxy import get_proxy_manager

from .provider import SearchProvider
from .rate_limiter import rate_limiter

logger = get_logger(__name__)
settings = Settings()

# Configure trafilatura for best extraction
TRAFILATURA_CONFIG = use_config()
TRAFILATURA_CONFIG.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")


class PlaywrightCrawler(SearchProvider):
    """Web crawler using Playwright with stealth mode.

    Features:
    - Headless Chrome/Chromium with stealth patches
    - JavaScript rendering for dynamic content
    - Automatic retry on failures
    - Content extraction with trafilatura
    - Respects robots.txt (configurable)
    """

    # Stealth user agents rotation
    USER_AGENTS = [
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
            "Gecko/20100101 Firefox/121.0"
        ),
    ]

    def __init__(
        self,
        headless: bool = True,
        timeout_ms: int = 30000,
        respect_robots: bool = True
    ) -> None:
        """Initialize the Playwright crawler.

        Args:
            headless: Run browser in headless mode
            timeout_ms: Default page load timeout in milliseconds
            respect_robots: Whether to check robots.txt (not implemented yet)
        """
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.respect_robots = respect_robots
        self._browser: Browser | None = None
        self._user_agent_index = 0

    @property
    def name(self) -> str:
        """Provider identifier for Playwright crawler."""
        return "playwright_crawler"

    @property
    def requests_per_second(self) -> float:
        """Rate limit: 0.5 RPS (1 request per 2 seconds to avoid blocks)."""
        return 0.5

    def _get_user_agent(self) -> str:
        """Rotate through user agents."""
        ua = self.USER_AGENTS[self._user_agent_index % len(self.USER_AGENTS)]
        self._user_agent_index += 1
        return ua

    async def _ensure_browser(self, proxy_config: dict | None = None) -> Browser:
        """Ensure browser is running, start if needed.

        Args:
            proxy_config: Optional Playwright proxy configuration dict
        """
        if self._browser is None or not self._browser.is_connected():
            playwright = await async_playwright().start()

            launch_options = {
                "headless": self.headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            }

            # Add proxy if configured
            if proxy_config:
                launch_options["proxy"] = proxy_config
                logger.debug("browser_using_proxy", proxy=proxy_config.get("server"))

            self._browser = await playwright.chromium.launch(**launch_options)
        return self._browser

    async def _create_stealth_page(self, target_domain: str | None = None) -> Page:
        """Create a new page with stealth settings.

        Args:
            target_domain: Target domain for proxy sticky sessions
        """
        # Get proxy configuration if available
        proxy_config = None
        proxy_manager = get_proxy_manager()
        current_proxy = None

        if proxy_manager and settings.proxy_enabled:
            current_proxy = await proxy_manager.get_proxy(domain=target_domain)
            if current_proxy:
                proxy_config = proxy_manager.get_playwright_config(current_proxy)

        browser = await self._ensure_browser(proxy_config)

        context = await browser.new_context(
            user_agent=self._get_user_agent(),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            # Stealth settings
            java_script_enabled=True,
            bypass_csp=True,
        )

        # Store proxy reference for success/failure tracking
        context._current_proxy = current_proxy  # type: ignore[attr-defined]

        page = await context.new_page()

        # Additional stealth: remove webdriver property
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Override permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );

            // Fake plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Fake languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        return page

    async def fetch_page(self, url: str) -> dict[str, Any]:
        """Fetch a single page and extract content.

        Args:
            url: URL to fetch

        Returns:
            dict with url, title, content, html, metadata

        Raises:
            TimeoutError: If page load times out
            AccessDeniedError: If access is denied (403, 401)
            RateLimitError: If rate limited (429)
        """
        from urllib.parse import urlparse

        await rate_limiter.acquire(self.name, self.requests_per_second)

        # Extract domain for proxy sticky sessions
        domain = urlparse(url).netloc

        page = await self._create_stealth_page(target_domain=domain)

        try:
            logger.info("crawler_fetch_start", url=url)

            # Navigate with wait for network idle
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.timeout_ms
            )

            # Check response status
            if response:
                status = response.status
                if status == 429:
                    raise RateLimitError(f"Rate limited by {url}", retry_after=60)
                elif status in (401, 403):
                    raise AccessDeniedError(f"Access denied to {url}: {status}")
                elif status >= 400:
                    logger.warning("crawler_http_error", url=url, status=status)
                    return {"url": url, "error": f"HTTP {status}"}

            # Wait a bit for JS to render
            await asyncio.sleep(0.5)

            # Get page content
            html = await page.content()
            title = await page.title()

            # Extract clean text with trafilatura
            extracted = extract(
                html,
                include_links=True,
                include_images=False,
                include_tables=True,
                output_format="txt",
                config=TRAFILATURA_CONFIG
            )

            # Get metadata
            metadata = await self._extract_metadata(page)

            logger.info(
                "crawler_fetch_complete",
                url=url,
                title=title[:50] if title else None,
                content_length=len(extracted) if extracted else 0
            )

            # Track proxy success
            proxy_manager = get_proxy_manager()
            current_proxy = getattr(page.context, "_current_proxy", None)
            if proxy_manager and current_proxy:
                await proxy_manager.mark_success(current_proxy)

            return {
                "url": url,
                "title": title or "",
                "content": extracted or "",
                "html": html,
                "metadata": metadata,
                "retrieved_at": datetime.now()
            }

        except PlaywrightTimeout as e:
            # Track proxy failure
            proxy_manager = get_proxy_manager()
            current_proxy = getattr(page.context, "_current_proxy", None)
            if proxy_manager and current_proxy:
                await proxy_manager.mark_failed(current_proxy, "timeout")

            logger.warning("crawler_timeout", url=url, error=str(e))
            raise TimeoutError(f"Timeout fetching {url}") from e

        except (AccessDeniedError, RateLimitError) as e:
            # Track proxy failure for access issues
            proxy_manager = get_proxy_manager()
            current_proxy = getattr(page.context, "_current_proxy", None)
            if proxy_manager and current_proxy:
                await proxy_manager.mark_failed(current_proxy, str(type(e).__name__))
            raise

        finally:
            await page.context.close()

    async def _extract_metadata(self, page: Page) -> dict[str, Any]:
        """Extract metadata from page (author, date, description)."""
        metadata: dict[str, Any] = {}

        with suppress(Exception):
            # Try common meta tags
            metadata["description"] = await page.evaluate("""
                () => {
                    const meta = document.querySelector('meta[name="description"]')
                        || document.querySelector('meta[property="og:description"]');
                    return meta ? meta.content : null;
                }
            """)

            metadata["author"] = await page.evaluate("""
                () => {
                    const meta = document.querySelector('meta[name="author"]')
                        || document.querySelector('meta[property="article:author"]');
                    return meta ? meta.content : null;
                }
            """)

            metadata["published_date"] = await page.evaluate("""
                () => {
                    const meta = document.querySelector('meta[property="article:published_time"]')
                        || document.querySelector('meta[name="date"]')
                        || document.querySelector('time[datetime]');
                    if (meta) {
                        return meta.content || meta.getAttribute('datetime');
                    }
                    return null;
                }
            """)

            metadata["canonical_url"] = await page.evaluate("""
                () => {
                    const link = document.querySelector('link[rel="canonical"]');
                    return link ? link.href : null;
                }
            """)

        return {k: v for k, v in metadata.items() if v}

    async def _do_search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Internal crawler search implementation.

        Note: This provider doesn't do traditional search. Instead, pass URLs
        in filters['urls'] to crawl them. The query is used for relevance filtering.

        Args:
            query: Search query (used for relevance)
            max_results: Maximum results to return
            filters: Must contain 'urls' key with list of URLs to crawl

        Returns:
            list[dict]: Crawled results in standardized format
        """
        filters = filters or {}
        urls = filters.get("urls", [])

        if not urls:
            logger.warning("crawler_no_urls", query=query)
            return []

        results = []

        for url in urls[:max_results]:
            try:
                page_data = await self.fetch_page(url)

                if "error" not in page_data and page_data.get("content"):
                    content = page_data["content"]
                    snippet = (content[:500] + "...") if len(content) > 500 else content
                    results.append({
                        "url": page_data["url"],
                        "title": page_data["title"],
                        "snippet": snippet,
                        "source_name": self.name,
                        "full_content": content,
                        "retrieved_at": page_data["retrieved_at"],
                        "metadata": page_data.get("metadata", {})
                    })

            except (TimeoutError, AccessDeniedError, RateLimitError) as e:
                logger.warning("crawler_url_failed", url=url, error=str(e))
                continue
            except Exception as e:
                logger.error("crawler_unexpected_error", url=url, error=str(e))
                continue

        return results

    async def crawl_search_results(
        self,
        search_results: list[dict[str, Any]],
        max_crawl: int = 5
    ) -> list[dict[str, Any]]:
        """Crawl full content for search results from other providers.

        This is the main integration point - takes results from Tavily/Brave/etc
        and fetches full content for them.

        Args:
            search_results: Results from other search providers
            max_crawl: Maximum number of URLs to crawl

        Returns:
            list[dict]: Enriched results with full content
        """
        enriched = []

        for i, result in enumerate(search_results):
            if i >= max_crawl:
                break

            url = result.get("url")
            if not url:
                enriched.append(result)
                continue

            # Skip if already has full content
            if result.get("full_content") and len(result["full_content"]) > 500:
                enriched.append(result)
                continue

            try:
                page_data = await self.fetch_page(url)

                if page_data.get("content"):
                    # Merge crawled content with original result
                    enriched_result = {
                        **result,
                        "full_content": page_data["content"],
                        "crawled": True,
                        "crawled_at": page_data["retrieved_at"],
                        "metadata": {
                            **result.get("metadata", {}),
                            **page_data.get("metadata", {})
                        }
                    }
                    enriched.append(enriched_result)
                else:
                    enriched.append(result)

            except Exception as e:
                logger.warning(
                    "crawler_enrich_failed",
                    url=url,
                    error=str(e)
                )
                enriched.append(result)

        return enriched

    async def is_available(self) -> bool:
        """Check if Playwright is available.

        Returns:
            bool: True if Playwright can be used
        """
        try:
            browser = await self._ensure_browser()
            return browser.is_connected()
        except Exception as e:
            logger.warning("crawler_not_available", error=str(e))
            return False

    async def close(self) -> None:
        """Close the browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
