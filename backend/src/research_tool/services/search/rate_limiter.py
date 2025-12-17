"""Rate limiter for search providers using token bucket algorithm.

Phase 6 Enhancement:
- Dual-layer rate limiting: provider-level AND domain-level
- Per-domain limits prevent hitting same domain from multiple providers
- robots.txt crawl-delay integration
"""

import asyncio
from collections import defaultdict
from time import time
from typing import Any

from research_tool.core.logging import get_logger

logger = get_logger(__name__)

# Default domain rate limit (requests per second)
DEFAULT_DOMAIN_RPS = 0.5  # 1 request per 2 seconds per domain

# Domain-specific rate limit overrides
DOMAIN_RATE_OVERRIDES: dict[str, float] = {
    # High-volume sites that can handle more traffic
    "google.com": 1.0,
    "wikipedia.org": 1.0,
    "github.com": 1.0,
    # Sites that need slower rates
    "scholar.google.com": 0.2,  # 1 request per 5 seconds
    "arxiv.org": 0.5,
}


class RateLimiter:
    """Token bucket rate limiter with dual-layer limiting.

    Phase 6 Enhancement:
    - Layer 1: Provider-level rate limiting (existing)
    - Layer 2: Domain-level rate limiting (new)

    This ensures the same domain isn't hit too frequently
    even when using multiple providers.
    """

    def __init__(
        self,
        default_domain_rps: float = DEFAULT_DOMAIN_RPS,
        domain_overrides: dict[str, float] | None = None
    ) -> None:
        """Initialize rate limiter with empty state.

        Args:
            default_domain_rps: Default requests per second per domain
            domain_overrides: Per-domain rate limit overrides
        """
        # Provider-level tracking
        self._last_request: dict[str, float] = defaultdict(float)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

        # Domain-level tracking (Phase 6)
        self._last_domain_request: dict[str, float] = defaultdict(float)
        self._domain_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._domain_crawl_delays: dict[str, float] = {}

        # Configuration
        self._default_domain_rps = default_domain_rps
        self._domain_overrides = domain_overrides or DOMAIN_RATE_OVERRIDES

    async def acquire(
        self,
        provider: str,
        requests_per_second: float,
        domain: str | None = None
    ) -> None:
        """Wait until request is allowed for the given provider and domain.

        Phase 6 Enhancement: Now includes domain-level rate limiting.

        Args:
            provider: Provider identifier
            requests_per_second: Maximum requests per second for this provider
            domain: Target domain (optional, for domain-level limiting)

        Example:
            await rate_limiter.acquire(
                "semantic_scholar", 1.0, "arxiv.org"
            )
        """
        # Layer 1: Provider-level limiting
        await self._acquire_provider(provider, requests_per_second)

        # Layer 2: Domain-level limiting (if domain provided)
        if domain:
            await self._acquire_domain(domain)

    async def _acquire_provider(
        self,
        provider: str,
        requests_per_second: float
    ) -> None:
        """Wait until provider-level rate limit allows request."""
        async with self._locks[provider]:
            min_interval = 1.0 / requests_per_second
            elapsed = time() - self._last_request[provider]

            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                await asyncio.sleep(wait_time)

            self._last_request[provider] = time()

    async def _acquire_domain(self, domain: str) -> None:
        """Wait until domain-level rate limit allows request.

        Uses crawl-delay if set, otherwise uses configured domain rate.
        """
        async with self._domain_locks[domain]:
            # Get domain-specific rate limit
            domain_rps = self._get_domain_rps(domain)
            min_interval = 1.0 / domain_rps

            elapsed = time() - self._last_domain_request[domain]

            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                logger.debug(
                    f"domain_rate_limit_wait: {domain} ({wait_time:.2f}s)"
                )
                await asyncio.sleep(wait_time)

            self._last_domain_request[domain] = time()

    def _get_domain_rps(self, domain: str) -> float:
        """Get rate limit for a specific domain.

        Priority:
        1. robots.txt crawl-delay (if set)
        2. Domain-specific override
        3. Default domain rate

        Args:
            domain: Domain to get rate for

        Returns:
            Requests per second allowed for this domain
        """
        # Check for crawl-delay from robots.txt
        if domain in self._domain_crawl_delays:
            crawl_delay = self._domain_crawl_delays[domain]
            return 1.0 / crawl_delay

        # Check for domain override (also check parent domains)
        for override_domain, rps in self._domain_overrides.items():
            if domain.endswith(override_domain):
                return rps

        return self._default_domain_rps

    def set_crawl_delay(self, domain: str, delay_seconds: float) -> None:
        """Set crawl-delay for a domain (from robots.txt).

        Args:
            domain: Domain to set delay for
            delay_seconds: Delay in seconds between requests
        """
        if delay_seconds > 0:
            self._domain_crawl_delays[domain] = delay_seconds
            logger.info(
                f"crawl_delay_set: {domain} = {delay_seconds}s"
            )

    def clear_crawl_delay(self, domain: str) -> None:
        """Clear crawl-delay for a domain.

        Args:
            domain: Domain to clear delay for
        """
        self._domain_crawl_delays.pop(domain, None)

    def reset(self, provider: str) -> None:
        """Reset rate limiting state for a provider.

        Args:
            provider: Provider identifier to reset
        """
        if provider in self._last_request:
            del self._last_request[provider]

    def reset_domain(self, domain: str) -> None:
        """Reset rate limiting state for a domain.

        Args:
            domain: Domain to reset
        """
        if domain in self._last_domain_request:
            del self._last_domain_request[domain]

    def get_domain_stats(self) -> dict[str, Any]:
        """Get current domain rate limiting statistics.

        Returns:
            dict with domain stats including last request times
        """
        return {
            "domains_tracked": len(self._last_domain_request),
            "crawl_delays_set": len(self._domain_crawl_delays),
            "domains": {
                domain: {
                    "last_request": self._last_domain_request.get(domain, 0),
                    "crawl_delay": self._domain_crawl_delays.get(domain),
                    "effective_rps": self._get_domain_rps(domain)
                }
                for domain in self._last_domain_request
            }
        }


# Global singleton instance
rate_limiter = RateLimiter()
