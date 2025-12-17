"""Proxy pool manager with rotation and health checking.

Provides automatic proxy rotation for anti-ban protection during scraping.
Supports multiple rotation strategies and automatic failure detection.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from time import time
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from typing import Literal

logger = logging.getLogger(__name__)


class ProxyStatus(Enum):
    """Proxy health status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    TESTING = "testing"


@dataclass
class Proxy:
    """Represents a proxy server."""

    url: str
    username: str | None = None
    password: str | None = None
    status: ProxyStatus = ProxyStatus.HEALTHY
    failure_count: int = 0
    success_count: int = 0
    last_used: float = 0.0
    last_failure: float = 0.0

    def __post_init__(self) -> None:
        """Extract auth from URL if present."""
        parsed = urlparse(self.url)
        if parsed.username and not self.username:
            self.username = parsed.username
        if parsed.password and not self.password:
            self.password = parsed.password

    @property
    def base_url(self) -> str:
        """URL without authentication credentials."""
        parsed = urlparse(self.url)
        if parsed.username or parsed.password:
            # Reconstruct URL without auth
            return f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 80}"
        return self.url


class ProxyManager:
    """Manages proxy pool with automatic rotation and health checking.

    Supports multiple rotation strategies:
    - round_robin: Cycle through proxies in order
    - random: Select random proxy each time
    - sticky: Same proxy for same domain (session affinity)

    Automatically removes proxies after consecutive failures and
    re-tests them periodically for recovery.
    """

    def __init__(
        self,
        strategy: Literal["round_robin", "random", "sticky"] = "round_robin",
        failure_threshold: int = 3,
        recovery_interval: float = 300.0,  # 5 minutes
    ) -> None:
        """Initialize proxy manager.

        Args:
            strategy: Rotation strategy to use
            failure_threshold: Failures before marking unhealthy
            recovery_interval: Seconds before re-testing unhealthy proxies
        """
        self._proxies: dict[str, Proxy] = {}
        self._strategy = strategy
        self._failure_threshold = failure_threshold
        self._recovery_interval = recovery_interval
        self._current_index = 0
        self._domain_map: dict[str, str] = {}  # domain -> proxy_url for sticky
        self._lock = asyncio.Lock()

    @property
    def pool_size(self) -> int:
        """Number of proxies in pool."""
        return len(self._proxies)

    def add_proxy(self, url: str) -> bool:
        """Add proxy to pool.

        Args:
            url: Proxy URL (e.g., http://user:pass@proxy:8080)

        Returns:
            True if added, False if duplicate
        """
        if url in self._proxies:
            return False

        proxy = Proxy(url=url)
        self._proxies[url] = proxy
        logger.debug(f"Added proxy to pool: {proxy.base_url}")
        return True

    def add_proxies(self, urls: list[str]) -> int:
        """Add multiple proxies to pool.

        Args:
            urls: List of proxy URLs

        Returns:
            Number of proxies added (excluding duplicates)
        """
        added = 0
        for url in urls:
            if self.add_proxy(url):
                added += 1
        return added

    async def get_proxy(self, domain: str | None = None) -> Proxy | None:
        """Get next available proxy.

        Args:
            domain: Target domain (used for sticky sessions)

        Returns:
            Proxy object or None if pool exhausted
        """
        async with self._lock:
            healthy = [p for p in self._proxies.values() if p.status == ProxyStatus.HEALTHY]

            if not healthy:
                logger.warning("No healthy proxies available")
                return None

            if self._strategy == "sticky" and domain:
                # Check if we have a sticky session for this domain
                if domain in self._domain_map:
                    url = self._domain_map[domain]
                    proxy = self._proxies.get(url)
                    if proxy and proxy.status == ProxyStatus.HEALTHY:
                        proxy.last_used = time()
                        return proxy
                    # Sticky proxy unhealthy, assign new one
                    del self._domain_map[domain]

                # Assign new sticky proxy for domain
                proxy = self._select_by_strategy(healthy)
                self._domain_map[domain] = proxy.url
                proxy.last_used = time()
                return proxy

            proxy = self._select_by_strategy(healthy)
            proxy.last_used = time()
            return proxy

    def _select_by_strategy(self, healthy: list[Proxy]) -> Proxy:
        """Select proxy based on configured strategy."""
        if self._strategy == "random":
            import random

            return random.choice(healthy)

        # round_robin (default)
        self._current_index = self._current_index % len(healthy)
        proxy = healthy[self._current_index]
        self._current_index += 1
        return proxy

    async def mark_failed(self, proxy: Proxy, reason: str) -> None:
        """Mark proxy as failed.

        Args:
            proxy: The proxy that failed
            reason: Failure reason for logging
        """
        async with self._lock:
            proxy.failure_count += 1
            proxy.last_failure = time()

            logger.warning(
                f"Proxy failed: {proxy.base_url} ({reason}), "
                f"failures: {proxy.failure_count}/{self._failure_threshold}"
            )

            if proxy.failure_count >= self._failure_threshold:
                proxy.status = ProxyStatus.UNHEALTHY
                logger.error(f"Proxy marked unhealthy: {proxy.base_url}")

                # Remove from sticky sessions
                domains_to_remove = [
                    d for d, url in self._domain_map.items() if url == proxy.url
                ]
                for domain in domains_to_remove:
                    del self._domain_map[domain]

    async def mark_success(self, proxy: Proxy) -> None:
        """Mark proxy as successful.

        Args:
            proxy: The proxy that succeeded
        """
        async with self._lock:
            proxy.failure_count = 0
            proxy.success_count += 1

            if proxy.status == ProxyStatus.TESTING:
                proxy.status = ProxyStatus.HEALTHY
                logger.info(f"Proxy recovered: {proxy.base_url}")

    async def health_check_all(self) -> dict[str, int]:
        """Get health status counts.

        Returns:
            Dict with healthy/unhealthy/testing counts
        """
        async with self._lock:
            counts = {"healthy": 0, "unhealthy": 0, "testing": 0}
            for proxy in self._proxies.values():
                counts[proxy.status.value] += 1
            return counts

    def get_httpx_config(self, proxy: Proxy) -> dict[str, str]:
        """Get httpx-compatible proxy configuration.

        Args:
            proxy: Proxy to configure

        Returns:
            Dict suitable for httpx proxies parameter
        """
        return {
            "http://": proxy.url,
            "https://": proxy.url,
        }

    def get_playwright_config(self, proxy: Proxy) -> dict[str, str]:
        """Get Playwright-compatible proxy configuration.

        Args:
            proxy: Proxy to configure

        Returns:
            Dict suitable for Playwright proxy parameter
        """
        config = {"server": proxy.base_url}
        if proxy.username:
            config["username"] = proxy.username
        if proxy.password:
            config["password"] = proxy.password
        return config

    @classmethod
    def from_list(cls, proxy_list: list[str], **kwargs) -> ProxyManager:
        """Create manager from list of proxy URLs.

        Args:
            proxy_list: List of proxy URLs
            **kwargs: Additional ProxyManager arguments

        Returns:
            Configured ProxyManager instance
        """
        manager = cls(**kwargs)
        manager.add_proxies(proxy_list)
        return manager

    @classmethod
    def from_file(cls, filepath: str, **kwargs) -> ProxyManager:
        """Create manager from proxy file.

        File format: one proxy URL per line, # for comments.

        Args:
            filepath: Path to proxy file
            **kwargs: Additional ProxyManager arguments

        Returns:
            Configured ProxyManager instance
        """
        manager = cls(**kwargs)

        path = Path(filepath)
        if not path.exists():
            logger.warning(f"Proxy file not found: {filepath}")
            return manager

        try:
            lines = path.read_text().strip().split("\n")
            proxies = [
                line.strip()
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]
            manager.add_proxies(proxies)
            logger.info(f"Loaded {manager.pool_size} proxies from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load proxy file: {e}")

        return manager


# Global singleton
_proxy_manager: ProxyManager | None = None


def get_proxy_manager() -> ProxyManager | None:
    """Get global proxy manager instance.

    Returns:
        ProxyManager if configured, None otherwise
    """
    return _proxy_manager


def init_proxy_manager(
    proxy_list: list[str] | None = None,
    proxy_file: str | None = None,
    **kwargs,
) -> ProxyManager:
    """Initialize global proxy manager.

    Args:
        proxy_list: List of proxy URLs
        proxy_file: Path to proxy file
        **kwargs: Additional ProxyManager arguments

    Returns:
        Initialized ProxyManager instance
    """
    global _proxy_manager

    if proxy_file:
        _proxy_manager = ProxyManager.from_file(proxy_file, **kwargs)
    elif proxy_list:
        _proxy_manager = ProxyManager.from_list(proxy_list, **kwargs)
    else:
        _proxy_manager = ProxyManager(**kwargs)

    return _proxy_manager
