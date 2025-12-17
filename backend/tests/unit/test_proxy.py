"""Unit tests for proxy rotation system."""

import pytest
from unittest.mock import patch

from research_tool.services.proxy.manager import ProxyManager, Proxy, ProxyStatus
from research_tool.services.proxy.providers import (
    EnvironmentProxyProvider,
    FileProxyProvider,
)


class TestProxy:
    """Test Proxy dataclass."""

    def test_proxy_creation(self):
        """Test creating a proxy."""
        proxy = Proxy(url="http://proxy1:8080")
        assert proxy.url == "http://proxy1:8080"
        assert proxy.status == ProxyStatus.HEALTHY
        assert proxy.failure_count == 0

    def test_proxy_with_auth(self):
        """Test proxy with authentication."""
        proxy = Proxy(url="http://user:pass@proxy1:8080")
        assert "user:pass" in proxy.url


class TestProxyManager:
    """Test ProxyManager class."""

    @pytest.fixture
    def manager(self):
        """Create a proxy manager with test proxies."""
        return ProxyManager(
            proxies=[
                "http://proxy1:8080",
                "http://proxy2:8080",
                "http://proxy3:8080",
            ],
            rotation_strategy="round_robin",
            failure_threshold=3,
        )

    def test_manager_initialization(self, manager):
        """Test manager initializes with proxies."""
        assert len(manager.proxies) == 3
        assert all(p.status == ProxyStatus.HEALTHY for p in manager.proxies)

    def test_manager_empty_proxies(self):
        """Test manager with no proxies returns None."""
        manager = ProxyManager(proxies=[])
        assert manager.get_proxy() is None

    def test_get_proxy_round_robin(self, manager):
        """Test round-robin rotation."""
        proxy1 = manager.get_proxy()
        proxy2 = manager.get_proxy()
        proxy3 = manager.get_proxy()
        proxy4 = manager.get_proxy()

        assert proxy1.url == "http://proxy1:8080"
        assert proxy2.url == "http://proxy2:8080"
        assert proxy3.url == "http://proxy3:8080"
        assert proxy4.url == "http://proxy1:8080"  # Wraps around

    def test_get_proxy_random(self):
        """Test random rotation."""
        manager = ProxyManager(
            proxies=["http://proxy1:8080", "http://proxy2:8080"],
            rotation_strategy="random",
        )
        proxy = manager.get_proxy()
        assert proxy is not None
        assert proxy.url in ["http://proxy1:8080", "http://proxy2:8080"]

    def test_mark_failed_increments_count(self, manager):
        """Test marking proxy as failed."""
        proxy = manager.get_proxy()
        manager.mark_failed(proxy, "connection_timeout")

        assert proxy.failure_count == 1
        assert proxy.status == ProxyStatus.HEALTHY

    def test_mark_failed_exceeds_threshold(self, manager):
        """Test proxy marked unhealthy after threshold."""
        proxy = manager.get_proxy()

        for _ in range(3):
            manager.mark_failed(proxy, "connection_timeout")

        assert proxy.failure_count == 3
        assert proxy.status == ProxyStatus.UNHEALTHY

    def test_unhealthy_proxy_skipped(self, manager):
        """Test unhealthy proxies are skipped in rotation."""
        proxy1 = manager.get_proxy()
        for _ in range(3):
            manager.mark_failed(proxy1, "banned")

        proxy2 = manager.get_proxy()
        assert proxy2.url == "http://proxy2:8080"

    def test_mark_success_resets_failure_count(self, manager):
        """Test successful request resets failure count."""
        proxy = manager.get_proxy()
        manager.mark_failed(proxy, "timeout")
        manager.mark_failed(proxy, "timeout")
        assert proxy.failure_count == 2

        manager.mark_success(proxy)
        assert proxy.failure_count == 0
        assert proxy.status == ProxyStatus.HEALTHY

    def test_all_proxies_unhealthy_returns_none(self, manager):
        """Test returns None when all proxies unhealthy."""
        for proxy in manager.proxies:
            for _ in range(3):
                manager.mark_failed(proxy, "banned")

        assert manager.get_proxy() is None

    def test_health_check_stats(self, manager):
        """Test health check returns correct stats."""
        proxy = manager.get_proxy()
        for _ in range(3):
            manager.mark_failed(proxy, "banned")

        stats = manager.get_health_stats()
        assert stats["healthy"] == 2
        assert stats["unhealthy"] == 1
        assert stats["total"] == 3

    def test_sticky_session_for_domain(self):
        """Test sticky session returns same proxy for domain."""
        manager = ProxyManager(
            proxies=["http://proxy1:8080", "http://proxy2:8080"],
            rotation_strategy="sticky",
        )

        proxy1 = manager.get_proxy(domain="example.com")
        proxy2 = manager.get_proxy(domain="example.com")

        assert proxy1.url == proxy2.url

    def test_to_playwright_format(self):
        """Test conversion to Playwright proxy format."""
        proxy = Proxy(url="http://user:pass@proxy1:8080")
        pw_proxy = proxy.to_playwright()

        assert pw_proxy["server"] == "http://proxy1:8080"
        assert pw_proxy["username"] == "user"
        assert pw_proxy["password"] == "pass"

    def test_to_httpx_format(self):
        """Test conversion to httpx proxy format."""
        proxy = Proxy(url="http://proxy1:8080")
        httpx_proxy = proxy.to_httpx()

        assert httpx_proxy == "http://proxy1:8080"


class TestEnvironmentProxyProvider:
    """Test loading proxies from environment."""

    def test_load_from_env_string(self):
        """Test loading comma-separated proxy list."""
        with patch.dict(
            "os.environ",
            {"PROXY_LIST": "http://p1:8080,http://p2:8080,http://p3:8080"},
        ):
            provider = EnvironmentProxyProvider()
            proxies = provider.get_proxies()

            assert len(proxies) == 3
            assert proxies[0] == "http://p1:8080"

    def test_load_empty_env(self):
        """Test empty environment returns empty list."""
        with patch.dict("os.environ", {}, clear=True):
            provider = EnvironmentProxyProvider()
            proxies = provider.get_proxies()
            assert proxies == []


class TestFileProxyProvider:
    """Test loading proxies from file."""

    def test_load_from_file(self, tmp_path):
        """Test loading proxies from file."""
        proxy_file = tmp_path / "proxies.txt"
        proxy_file.write_text("http://p1:8080\nhttp://p2:8080\n# comment\nhttp://p3:8080")

        provider = FileProxyProvider(str(proxy_file))
        proxies = provider.get_proxies()

        assert len(proxies) == 3
        assert "http://p1:8080" in proxies

    def test_file_not_found(self):
        """Test missing file returns empty list."""
        provider = FileProxyProvider("/nonexistent/proxies.txt")
        proxies = provider.get_proxies()
        assert proxies == []

    def test_empty_file(self, tmp_path):
        """Test empty file returns empty list."""
        proxy_file = tmp_path / "empty.txt"
        proxy_file.write_text("")

        provider = FileProxyProvider(str(proxy_file))
        proxies = provider.get_proxies()
        assert proxies == []
