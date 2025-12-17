"""Unit tests for robots.txt compliance system."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

from research_tool.services.compliance.robots import RobotsChecker
from research_tool.services.compliance.cache import RobotsCache


class TestRobotsChecker:
    """Test RobotsChecker class."""

    @pytest.fixture
    def checker(self):
        """Create a robots checker."""
        return RobotsChecker(user_agent="TestBot/1.0")

    @pytest.mark.asyncio
    async def test_can_fetch_allowed(self, checker):
        """Test allowed URL returns True."""
        robots_content = """
User-agent: *
Allow: /

User-agent: BadBot
Disallow: /
"""
        with patch.object(checker, "_fetch_robots", return_value=robots_content):
            result = await checker.can_fetch("https://example.com/page")
            assert result is True

    @pytest.mark.asyncio
    async def test_can_fetch_disallowed(self, checker):
        """Test disallowed URL returns False."""
        robots_content = """
User-agent: *
Disallow: /private/
"""
        with patch.object(checker, "_fetch_robots", return_value=robots_content):
            result = await checker.can_fetch("https://example.com/private/secret")
            assert result is False

    @pytest.mark.asyncio
    async def test_can_fetch_specific_user_agent(self, checker):
        """Test specific user-agent rules."""
        robots_content = """
User-agent: TestBot
Disallow: /blocked/

User-agent: *
Allow: /
"""
        with patch.object(checker, "_fetch_robots", return_value=robots_content):
            # TestBot should be blocked
            result = await checker.can_fetch("https://example.com/blocked/page")
            assert result is False

    @pytest.mark.asyncio
    async def test_can_fetch_wildcard_pattern(self, checker):
        """Test wildcard patterns in robots.txt."""
        robots_content = """
User-agent: *
Disallow: /*.pdf$
Disallow: /temp*
"""
        with patch.object(checker, "_fetch_robots", return_value=robots_content):
            # PDF should be blocked
            result = await checker.can_fetch("https://example.com/doc.pdf")
            assert result is False

            # temp* should be blocked
            result = await checker.can_fetch("https://example.com/temporary")
            assert result is False

            # Regular page allowed
            result = await checker.can_fetch("https://example.com/page")
            assert result is True

    @pytest.mark.asyncio
    async def test_get_crawl_delay(self, checker):
        """Test crawl-delay extraction."""
        robots_content = """
User-agent: *
Crawl-delay: 5
Disallow: /private/
"""
        with patch.object(checker, "_fetch_robots", return_value=robots_content):
            delay = await checker.get_crawl_delay("https://example.com")
            assert delay == 5.0

    @pytest.mark.asyncio
    async def test_get_crawl_delay_none(self, checker):
        """Test no crawl-delay returns None."""
        robots_content = """
User-agent: *
Disallow: /private/
"""
        with patch.object(checker, "_fetch_robots", return_value=robots_content):
            delay = await checker.get_crawl_delay("https://example.com")
            assert delay is None

    @pytest.mark.asyncio
    async def test_get_sitemap_urls(self, checker):
        """Test sitemap extraction."""
        robots_content = """
User-agent: *
Allow: /

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap2.xml
"""
        with patch.object(checker, "_fetch_robots", return_value=robots_content):
            sitemaps = await checker.get_sitemap_urls("https://example.com")
            assert len(sitemaps) == 2
            assert "https://example.com/sitemap.xml" in sitemaps

    @pytest.mark.asyncio
    async def test_robots_not_found_allows(self, checker):
        """Test missing robots.txt allows access."""
        with patch.object(checker, "_fetch_robots", return_value=None):
            result = await checker.can_fetch("https://example.com/page")
            assert result is True

    @pytest.mark.asyncio
    async def test_robots_error_allows_with_config(self):
        """Test error fetching robots.txt respects config."""
        checker = RobotsChecker(user_agent="TestBot", allow_on_error=True)
        with patch.object(checker, "_fetch_robots", side_effect=Exception("Network error")):
            result = await checker.can_fetch("https://example.com/page")
            assert result is True

    @pytest.mark.asyncio
    async def test_robots_error_blocks_with_config(self):
        """Test error fetching robots.txt respects config."""
        checker = RobotsChecker(user_agent="TestBot", allow_on_error=False)
        with patch.object(checker, "_fetch_robots", side_effect=Exception("Network error")):
            result = await checker.can_fetch("https://example.com/page")
            assert result is False


class TestRobotsCache:
    """Test RobotsCache class."""

    @pytest.fixture
    def cache(self):
        """Create a robots cache."""
        return RobotsCache(max_size=100, ttl_seconds=3600)

    def test_cache_set_get(self, cache):
        """Test basic cache set/get."""
        cache.set("example.com", "User-agent: *\nDisallow:")
        result = cache.get("example.com")
        assert result == "User-agent: *\nDisallow:"

    def test_cache_miss(self, cache):
        """Test cache miss returns None."""
        result = cache.get("unknown.com")
        assert result is None

    def test_cache_expiry(self, cache):
        """Test expired entries return None."""
        cache = RobotsCache(max_size=100, ttl_seconds=0)  # Immediate expiry
        cache.set("example.com", "content")

        import time
        time.sleep(0.1)

        result = cache.get("example.com")
        assert result is None

    def test_cache_clear_domain(self, cache):
        """Test clearing specific domain."""
        cache.set("example.com", "content1")
        cache.set("other.com", "content2")

        cache.clear("example.com")

        assert cache.get("example.com") is None
        assert cache.get("other.com") == "content2"

    def test_cache_clear_all(self, cache):
        """Test clearing all domains."""
        cache.set("example.com", "content1")
        cache.set("other.com", "content2")

        cache.clear()

        assert cache.get("example.com") is None
        assert cache.get("other.com") is None

    def test_cache_lru_eviction(self):
        """Test LRU eviction when max size reached."""
        cache = RobotsCache(max_size=2, ttl_seconds=3600)

        cache.set("first.com", "1")
        cache.set("second.com", "2")
        cache.set("third.com", "3")  # Should evict first.com

        assert cache.get("first.com") is None
        assert cache.get("second.com") == "2"
        assert cache.get("third.com") == "3"

    def test_cache_stats(self, cache):
        """Test cache statistics."""
        cache.set("example.com", "content")
        cache.get("example.com")  # Hit
        cache.get("unknown.com")  # Miss

        stats = cache.get_stats()
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
