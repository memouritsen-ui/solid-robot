"""Tests for proxy rotation system."""

from unittest.mock import AsyncMock, patch

import pytest

from research_tool.services.proxy.manager import Proxy, ProxyManager, ProxyStatus


class TestProxy:
    """Test Proxy dataclass."""

    def test_proxy_creation(self) -> None:
        """Proxy can be created with required fields."""
        proxy = Proxy(url="http://proxy1:8080")
        assert proxy.url == "http://proxy1:8080"
        assert proxy.status == ProxyStatus.HEALTHY
        assert proxy.failure_count == 0
        assert proxy.success_count == 0

    def test_proxy_with_auth(self) -> None:
        """Proxy can include authentication."""
        proxy = Proxy(
            url="http://user:pass@proxy1:8080",
            username="user",
            password="pass",
        )
        assert proxy.username == "user"
        assert proxy.password == "pass"

    def test_proxy_status_transitions(self) -> None:
        """Proxy status can transition between states."""
        proxy = Proxy(url="http://proxy1:8080")
        assert proxy.status == ProxyStatus.HEALTHY

        proxy.status = ProxyStatus.UNHEALTHY
        assert proxy.status == ProxyStatus.UNHEALTHY

        proxy.status = ProxyStatus.TESTING
        assert proxy.status == ProxyStatus.TESTING


class TestProxyManager:
    """Test ProxyManager class."""

    def test_manager_empty_pool(self) -> None:
        """Manager can be created with empty pool."""
        manager = ProxyManager()
        assert manager.pool_size == 0

    def test_manager_add_proxy(self) -> None:
        """Manager can add proxies to pool."""
        manager = ProxyManager()
        manager.add_proxy("http://proxy1:8080")
        assert manager.pool_size == 1

    def test_manager_add_multiple_proxies(self) -> None:
        """Manager can add multiple proxies."""
        manager = ProxyManager()
        manager.add_proxies([
            "http://proxy1:8080",
            "http://proxy2:8080",
            "http://proxy3:8080",
        ])
        assert manager.pool_size == 3

    def test_manager_no_duplicate_proxies(self) -> None:
        """Manager rejects duplicate proxy URLs."""
        manager = ProxyManager()
        manager.add_proxy("http://proxy1:8080")
        manager.add_proxy("http://proxy1:8080")
        assert manager.pool_size == 1

    @pytest.mark.asyncio
    async def test_get_proxy_returns_healthy(self) -> None:
        """get_proxy returns a healthy proxy."""
        manager = ProxyManager()
        manager.add_proxy("http://proxy1:8080")

        proxy = await manager.get_proxy()
        assert proxy is not None
        assert proxy.url == "http://proxy1:8080"
        assert proxy.status == ProxyStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_get_proxy_empty_pool_returns_none(self) -> None:
        """get_proxy returns None when pool is empty."""
        manager = ProxyManager()
        proxy = await manager.get_proxy()
        assert proxy is None

    @pytest.mark.asyncio
    async def test_get_proxy_round_robin(self) -> None:
        """get_proxy rotates through proxies in round-robin."""
        manager = ProxyManager(strategy="round_robin")
        manager.add_proxies([
            "http://proxy1:8080",
            "http://proxy2:8080",
            "http://proxy3:8080",
        ])

        # Should cycle through all proxies
        urls = []
        for _ in range(6):
            proxy = await manager.get_proxy()
            urls.append(proxy.url)

        # Each proxy should appear twice
        assert urls.count("http://proxy1:8080") == 2
        assert urls.count("http://proxy2:8080") == 2
        assert urls.count("http://proxy3:8080") == 2

    @pytest.mark.asyncio
    async def test_mark_failed_increments_count(self) -> None:
        """mark_failed increments failure count."""
        manager = ProxyManager()
        manager.add_proxy("http://proxy1:8080")

        proxy = await manager.get_proxy()
        await manager.mark_failed(proxy, "connection timeout")

        assert proxy.failure_count == 1

    @pytest.mark.asyncio
    async def test_mark_failed_removes_after_threshold(self) -> None:
        """mark_failed removes proxy after 3 consecutive failures."""
        manager = ProxyManager(failure_threshold=3)
        manager.add_proxy("http://proxy1:8080")

        proxy = await manager.get_proxy()

        # Fail 3 times
        await manager.mark_failed(proxy, "timeout")
        await manager.mark_failed(proxy, "timeout")
        await manager.mark_failed(proxy, "timeout")

        assert proxy.status == ProxyStatus.UNHEALTHY
        # Should not be returned by get_proxy
        assert await manager.get_proxy() is None

    @pytest.mark.asyncio
    async def test_mark_success_resets_failure_count(self) -> None:
        """mark_success resets failure count to zero."""
        manager = ProxyManager()
        manager.add_proxy("http://proxy1:8080")

        proxy = await manager.get_proxy()
        await manager.mark_failed(proxy, "timeout")
        await manager.mark_failed(proxy, "timeout")
        assert proxy.failure_count == 2

        await manager.mark_success(proxy)
        assert proxy.failure_count == 0
        assert proxy.success_count == 1

    @pytest.mark.asyncio
    async def test_mark_success_recovers_unhealthy(self) -> None:
        """mark_success can recover an unhealthy proxy in testing state."""
        manager = ProxyManager(failure_threshold=3)
        manager.add_proxy("http://proxy1:8080")

        proxy = await manager.get_proxy()

        # Make unhealthy
        for _ in range(3):
            await manager.mark_failed(proxy, "timeout")
        assert proxy.status == ProxyStatus.UNHEALTHY

        # Manually set to testing (simulating health check)
        proxy.status = ProxyStatus.TESTING

        # Success should recover it
        await manager.mark_success(proxy)
        assert proxy.status == ProxyStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_get_proxy_skips_unhealthy(self) -> None:
        """get_proxy skips unhealthy proxies."""
        manager = ProxyManager(failure_threshold=3)
        manager.add_proxies([
            "http://proxy1:8080",
            "http://proxy2:8080",
        ])

        # Make first proxy unhealthy
        proxy1 = await manager.get_proxy()
        for _ in range(3):
            await manager.mark_failed(proxy1, "timeout")

        # Should only return proxy2 now
        for _ in range(3):
            proxy = await manager.get_proxy()
            assert proxy.url == "http://proxy2:8080"

    @pytest.mark.asyncio
    async def test_health_check_all(self) -> None:
        """health_check_all returns status counts."""
        manager = ProxyManager(failure_threshold=3)
        manager.add_proxies([
            "http://proxy1:8080",
            "http://proxy2:8080",
            "http://proxy3:8080",
        ])

        # Make one unhealthy
        proxy = await manager.get_proxy()
        for _ in range(3):
            await manager.mark_failed(proxy, "timeout")

        status = await manager.health_check_all()
        assert status["healthy"] == 2
        assert status["unhealthy"] == 1

    @pytest.mark.asyncio
    async def test_sticky_session_returns_same_proxy(self) -> None:
        """Sticky sessions return same proxy for same domain."""
        manager = ProxyManager(strategy="sticky")
        manager.add_proxies([
            "http://proxy1:8080",
            "http://proxy2:8080",
        ])

        # Same domain should get same proxy
        proxy1 = await manager.get_proxy(domain="example.com")
        proxy2 = await manager.get_proxy(domain="example.com")
        assert proxy1.url == proxy2.url

        # Different domain may get different proxy
        proxy3 = await manager.get_proxy(domain="other.com")
        # (may or may not be same, just testing no crash)
        assert proxy3 is not None


class TestProxyManagerFromConfig:
    """Test ProxyManager configuration loading."""

    def test_from_list(self) -> None:
        """Manager can be created from proxy list."""
        proxy_list = [
            "http://proxy1:8080",
            "http://proxy2:8080",
        ]
        manager = ProxyManager.from_list(proxy_list)
        assert manager.pool_size == 2

    def test_from_file(self, tmp_path) -> None:
        """Manager can be created from proxy file."""
        proxy_file = tmp_path / "proxies.txt"
        proxy_file.write_text(
            "http://proxy1:8080\n"
            "http://proxy2:8080\n"
            "# This is a comment\n"
            "http://proxy3:8080\n"
        )

        manager = ProxyManager.from_file(str(proxy_file))
        assert manager.pool_size == 3

    def test_from_file_empty(self, tmp_path) -> None:
        """Manager handles empty proxy file."""
        proxy_file = tmp_path / "proxies.txt"
        proxy_file.write_text("")

        manager = ProxyManager.from_file(str(proxy_file))
        assert manager.pool_size == 0

    def test_from_file_not_found(self) -> None:
        """Manager handles missing proxy file gracefully."""
        manager = ProxyManager.from_file("/nonexistent/proxies.txt")
        assert manager.pool_size == 0


class TestProxyManagerIntegration:
    """Integration tests for proxy manager with HTTP clients."""

    @pytest.mark.asyncio
    async def test_get_httpx_proxy_config(self) -> None:
        """Manager returns httpx-compatible proxy config."""
        manager = ProxyManager()
        manager.add_proxy("http://proxy1:8080")

        proxy = await manager.get_proxy()
        config = manager.get_httpx_config(proxy)

        assert "http://" in config or "https://" in config
        assert config.get("http://") == "http://proxy1:8080"

    @pytest.mark.asyncio
    async def test_get_playwright_proxy_config(self) -> None:
        """Manager returns Playwright-compatible proxy config."""
        manager = ProxyManager()
        manager.add_proxy("http://user:pass@proxy1:8080")

        proxy = await manager.get_proxy()
        config = manager.get_playwright_config(proxy)

        assert config["server"] == "http://proxy1:8080"
        assert config["username"] == "user"
        assert config["password"] == "pass"
