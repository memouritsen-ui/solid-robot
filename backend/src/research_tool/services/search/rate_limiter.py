"""Rate limiter for search providers using token bucket algorithm."""

import asyncio
from collections import defaultdict
from time import time


class RateLimiter:
    """Token bucket rate limiter per provider.

    Ensures each provider respects its rate limit by tracking
    the last request time and enforcing minimum intervals.
    """

    def __init__(self) -> None:
        """Initialize rate limiter with empty state."""
        self._last_request: dict[str, float] = defaultdict(float)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def acquire(self, provider: str, requests_per_second: float) -> None:
        """Wait until request is allowed for the given provider.

        Args:
            provider: Provider identifier
            requests_per_second: Maximum requests per second for this provider

        Example:
            await rate_limiter.acquire("semantic_scholar", 1.0)  # Wait if needed
            # Now safe to make request
        """
        async with self._locks[provider]:
            min_interval = 1.0 / requests_per_second
            elapsed = time() - self._last_request[provider]

            if elapsed < min_interval:
                # Need to wait
                wait_time = min_interval - elapsed
                await asyncio.sleep(wait_time)

            self._last_request[provider] = time()

    def reset(self, provider: str) -> None:
        """Reset rate limiting state for a provider.

        Args:
            provider: Provider identifier to reset
        """
        if provider in self._last_request:
            del self._last_request[provider]


# Global singleton instance
rate_limiter = RateLimiter()
