"""LRU cache for robots.txt content."""

import time
from collections import OrderedDict
from dataclasses import dataclass

from research_tool.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Entry in the robots.txt cache."""

    content: str
    timestamp: float


class RobotsCache:
    """LRU cache for robots.txt content with TTL."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 86400):
        """Initialize cache.

        Args:
            max_size: Maximum number of domains to cache
            ttl_seconds: Time-to-live in seconds (default 24 hours)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, domain: str) -> str | None:
        """Get cached robots.txt content.

        Args:
            domain: Domain to look up

        Returns:
            Cached content or None if not found/expired
        """
        entry = self._cache.get(domain)

        if entry is None:
            self._misses += 1
            return None

        # Check if expired
        if time.time() - entry.timestamp > self.ttl_seconds:
            del self._cache[domain]
            self._misses += 1
            logger.debug("robots_cache_expired", domain=domain)
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(domain)
        self._hits += 1
        return entry.content

    def set(self, domain: str, content: str) -> None:
        """Cache robots.txt content.

        Args:
            domain: Domain to cache
            content: robots.txt content
        """
        # Remove oldest if at capacity
        while len(self._cache) >= self.max_size:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
            logger.debug("robots_cache_evicted", domain=oldest)

        self._cache[domain] = CacheEntry(
            content=content,
            timestamp=time.time(),
        )
        logger.debug("robots_cache_set", domain=domain)

    def clear(self, domain: str | None = None) -> None:
        """Clear cache entries.

        Args:
            domain: Specific domain to clear, or None to clear all
        """
        if domain:
            if domain in self._cache:
                del self._cache[domain]
                logger.debug("robots_cache_cleared", domain=domain)
        else:
            self._cache.clear()
            logger.info("robots_cache_cleared_all")

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            dict with size, hits, misses
        """
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
        }
