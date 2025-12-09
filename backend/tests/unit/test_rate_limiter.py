"""Tests for rate limiter."""

import asyncio
from time import time

import pytest

from research_tool.services.search.rate_limiter import RateLimiter, rate_limiter


class TestRateLimiter:
    """Test suite for RateLimiter class."""

    def test_init_creates_empty_state(self) -> None:
        """RateLimiter initializes with empty state."""
        limiter = RateLimiter()
        assert limiter._last_request is not None
        assert limiter._locks is not None

    @pytest.mark.asyncio
    async def test_acquire_allows_first_request(self) -> None:
        """First request is allowed immediately."""
        limiter = RateLimiter()
        start = time()
        await limiter.acquire("test_provider", 1.0)
        elapsed = time() - start
        # Should be nearly instant (< 100ms)
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_acquire_rate_limits_subsequent_requests(self) -> None:
        """Subsequent requests are rate limited."""
        limiter = RateLimiter()

        # First request - immediate
        await limiter.acquire("test_provider", 2.0)  # 2 RPS = 0.5s interval

        # Second request - should wait
        start = time()
        await limiter.acquire("test_provider", 2.0)
        elapsed = time() - start

        # Should wait approximately 0.5 seconds
        assert elapsed >= 0.4  # Allow some tolerance
        assert elapsed < 0.7

    @pytest.mark.asyncio
    async def test_acquire_different_providers_independent(self) -> None:
        """Different providers have independent rate limits."""
        limiter = RateLimiter()

        # First request to provider A
        await limiter.acquire("provider_a", 1.0)

        # First request to provider B - should be immediate
        start = time()
        await limiter.acquire("provider_b", 1.0)
        elapsed = time() - start

        assert elapsed < 0.1  # Should be nearly instant

    @pytest.mark.asyncio
    async def test_acquire_respects_requests_per_second(self) -> None:
        """Rate limiter respects different RPS values."""
        limiter = RateLimiter()

        # 10 RPS = 0.1s interval
        await limiter.acquire("fast_provider", 10.0)
        start = time()
        await limiter.acquire("fast_provider", 10.0)
        fast_elapsed = time() - start

        # Reset for slow provider test
        limiter = RateLimiter()

        # 1 RPS = 1.0s interval
        await limiter.acquire("slow_provider", 1.0)
        start = time()
        await limiter.acquire("slow_provider", 1.0)
        slow_elapsed = time() - start

        # Slow provider should wait longer
        assert slow_elapsed > fast_elapsed

    def test_reset_clears_provider_state(self) -> None:
        """reset clears state for specific provider."""
        limiter = RateLimiter()
        limiter._last_request["test"] = time()

        limiter.reset("test")

        assert "test" not in limiter._last_request

    def test_reset_nonexistent_provider_no_error(self) -> None:
        """reset on nonexistent provider doesn't raise."""
        limiter = RateLimiter()
        # Should not raise
        limiter.reset("nonexistent")

    @pytest.mark.asyncio
    async def test_concurrent_requests_serialized(self) -> None:
        """Concurrent requests to same provider are serialized."""
        limiter = RateLimiter()
        request_times: list[float] = []

        async def make_request() -> None:
            await limiter.acquire("concurrent_test", 5.0)  # 5 RPS = 0.2s
            request_times.append(time())

        # Launch 3 concurrent requests
        await asyncio.gather(
            make_request(),
            make_request(),
            make_request()
        )

        # Requests should be spaced at least 0.15s apart (with tolerance)
        assert len(request_times) == 3
        request_times.sort()

        for i in range(1, len(request_times)):
            gap = request_times[i] - request_times[i-1]
            assert gap >= 0.15  # Allow some tolerance


class TestGlobalRateLimiter:
    """Test the global rate_limiter singleton."""

    def test_global_instance_exists(self) -> None:
        """Global rate_limiter instance is available."""
        assert rate_limiter is not None
        assert isinstance(rate_limiter, RateLimiter)

    @pytest.mark.asyncio
    async def test_global_instance_works(self) -> None:
        """Global rate_limiter can be used for requests."""
        # Reset state first
        rate_limiter.reset("global_test")

        start = time()
        await rate_limiter.acquire("global_test", 10.0)
        elapsed = time() - start

        assert elapsed < 0.1  # First request should be fast
