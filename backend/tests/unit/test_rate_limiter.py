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


class TestDomainRateLimiting:
    """Test suite for Phase 6 domain-level rate limiting."""

    @pytest.mark.asyncio
    async def test_acquire_with_domain_applies_both_limits(self) -> None:
        """acquire with domain applies both provider and domain limits."""
        limiter = RateLimiter()

        # First request - immediate
        start = time()
        await limiter.acquire("provider", 10.0, domain="example.com")
        elapsed = time() - start
        assert elapsed < 0.1

        # Domain tracked
        assert "example.com" in limiter._last_domain_request

    @pytest.mark.asyncio
    async def test_domain_rate_limit_independent_of_provider(self) -> None:
        """Same domain from different providers still rate limited."""
        limiter = RateLimiter(default_domain_rps=2.0)  # 0.5s interval

        # Provider A hits domain
        await limiter.acquire("provider_a", 10.0, domain="shared.com")

        # Provider B hits same domain - should wait for domain limit
        start = time()
        await limiter.acquire("provider_b", 10.0, domain="shared.com")
        elapsed = time() - start

        # Should wait approximately 0.5s for domain limit
        assert elapsed >= 0.4
        assert elapsed < 0.7

    @pytest.mark.asyncio
    async def test_different_domains_independent(self) -> None:
        """Different domains have independent limits."""
        limiter = RateLimiter(default_domain_rps=1.0)

        # Hit domain A
        await limiter.acquire("provider", 10.0, domain="domain-a.com")

        # Hit domain B - should be immediate
        start = time()
        await limiter.acquire("provider", 10.0, domain="domain-b.com")
        elapsed = time() - start

        assert elapsed < 0.2  # Allow tolerance for slow CI

    def test_set_crawl_delay(self) -> None:
        """set_crawl_delay stores delay for domain."""
        limiter = RateLimiter()

        limiter.set_crawl_delay("slow-site.com", 5.0)

        assert "slow-site.com" in limiter._domain_crawl_delays
        assert limiter._domain_crawl_delays["slow-site.com"] == 5.0

    def test_set_crawl_delay_ignored_if_zero(self) -> None:
        """set_crawl_delay ignores zero or negative delays."""
        limiter = RateLimiter()

        limiter.set_crawl_delay("site.com", 0)
        limiter.set_crawl_delay("other.com", -1)

        assert "site.com" not in limiter._domain_crawl_delays
        assert "other.com" not in limiter._domain_crawl_delays

    def test_clear_crawl_delay(self) -> None:
        """clear_crawl_delay removes domain delay."""
        limiter = RateLimiter()
        limiter.set_crawl_delay("site.com", 3.0)

        limiter.clear_crawl_delay("site.com")

        assert "site.com" not in limiter._domain_crawl_delays

    def test_clear_crawl_delay_nonexistent_no_error(self) -> None:
        """clear_crawl_delay on nonexistent domain doesn't raise."""
        limiter = RateLimiter()
        # Should not raise
        limiter.clear_crawl_delay("nonexistent.com")

    @pytest.mark.asyncio
    async def test_crawl_delay_respected(self) -> None:
        """Crawl-delay from robots.txt is respected."""
        limiter = RateLimiter()
        limiter.set_crawl_delay("slow.com", 0.5)  # 0.5s delay = 2 RPS

        # First request
        await limiter.acquire("provider", 10.0, domain="slow.com")

        # Second request - should wait for crawl-delay
        start = time()
        await limiter.acquire("provider", 10.0, domain="slow.com")
        elapsed = time() - start

        assert elapsed >= 0.4
        assert elapsed < 0.7

    def test_get_domain_rps_default(self) -> None:
        """_get_domain_rps returns default for unknown domain."""
        limiter = RateLimiter(default_domain_rps=0.5)

        rps = limiter._get_domain_rps("unknown.com")

        assert rps == 0.5

    def test_get_domain_rps_override(self) -> None:
        """_get_domain_rps returns override for known domain."""
        overrides = {"fast.com": 5.0, "slow.com": 0.1}
        limiter = RateLimiter(domain_overrides=overrides)

        assert limiter._get_domain_rps("fast.com") == 5.0
        assert limiter._get_domain_rps("slow.com") == 0.1

    def test_get_domain_rps_subdomain_matching(self) -> None:
        """_get_domain_rps matches subdomains."""
        overrides = {"google.com": 2.0}
        limiter = RateLimiter(domain_overrides=overrides)

        # Subdomain should match parent
        assert limiter._get_domain_rps("www.google.com") == 2.0
        assert limiter._get_domain_rps("scholar.google.com") == 2.0

    def test_get_domain_rps_crawl_delay_priority(self) -> None:
        """Crawl-delay takes priority over override."""
        overrides = {"site.com": 10.0}  # Override says 10 RPS
        limiter = RateLimiter(domain_overrides=overrides)
        limiter.set_crawl_delay("site.com", 5.0)  # Crawl-delay says 0.2 RPS

        # Crawl-delay should win
        assert limiter._get_domain_rps("site.com") == 0.2  # 1/5 = 0.2

    def test_reset_domain(self) -> None:
        """reset_domain clears state for specific domain."""
        limiter = RateLimiter()
        limiter._last_domain_request["test.com"] = time()

        limiter.reset_domain("test.com")

        assert "test.com" not in limiter._last_domain_request

    def test_reset_domain_nonexistent_no_error(self) -> None:
        """reset_domain on nonexistent domain doesn't raise."""
        limiter = RateLimiter()
        # Should not raise
        limiter.reset_domain("nonexistent.com")

    def test_get_domain_stats(self) -> None:
        """get_domain_stats returns domain statistics."""
        limiter = RateLimiter(default_domain_rps=1.0)
        limiter._last_domain_request["example.com"] = 12345.0
        limiter.set_crawl_delay("slow.com", 5.0)

        stats = limiter.get_domain_stats()

        assert stats["domains_tracked"] == 1
        assert stats["crawl_delays_set"] == 1
        assert "example.com" in stats["domains"]
        assert stats["domains"]["example.com"]["last_request"] == 12345.0


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
