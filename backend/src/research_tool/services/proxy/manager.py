"""Proxy pool management with automatic rotation and health checking."""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from research_tool.core.logging import get_logger

logger = get_logger(__name__)


class ProxyStatus(Enum):
    """Status of a proxy in the pool."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    TESTING = "testing"


@dataclass
class Proxy:
    """Represents a proxy server with health tracking."""

    url: str
    status: ProxyStatus = ProxyStatus.HEALTHY
    failure_count: int = 0
    last_used: float = 0.0
    last_failure_reason: str = ""

    def to_playwright(self) -> dict[str, Any]:
        """Convert to Playwright proxy format.

        Returns:
            dict with server, username, password keys
        """
        parsed = urlparse(self.url)

        result: dict[str, Any] = {
            "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 8080}"
        }

        if parsed.username:
            result["username"] = parsed.username
        if parsed.password:
            result["password"] = parsed.password

        return result

    def to_httpx(self) -> str:
        """Convert to httpx proxy format.

        Returns:
            Proxy URL string
        """
        return self.url


class ProxyManager:
    """Manages proxy pool with automatic rotation and health checking."""

    def __init__(
        self,
        proxies: list[str] | None = None,
        rotation_strategy: str = "round_robin",
        failure_threshold: int = 3,
    ):
        """Initialize proxy manager.

        Args:
            proxies: List of proxy URLs
            rotation_strategy: round_robin, random, or sticky
            failure_threshold: Failures before marking unhealthy
        """
        self.proxies: list[Proxy] = []
        self.rotation_strategy = rotation_strategy
        self.failure_threshold = failure_threshold
        self._current_index = 0
        self._domain_proxy_map: dict[str, Proxy] = {}

        if proxies:
            for proxy_url in proxies:
                self.proxies.append(Proxy(url=proxy_url))

        logger.info(
            "proxy_manager_initialized",
            proxy_count=len(self.proxies),
            rotation_strategy=rotation_strategy,
        )

    def get_proxy(self, domain: str | None = None) -> Proxy | None:
        """Get next proxy using configured rotation strategy.

        Args:
            domain: Optional domain for sticky sessions

        Returns:
            Proxy instance or None if no healthy proxies
        """
        healthy_proxies = [p for p in self.proxies if p.status == ProxyStatus.HEALTHY]

        if not healthy_proxies:
            logger.warning("no_healthy_proxies_available")
            return None

        if self.rotation_strategy == "sticky" and domain:
            return self._get_sticky_proxy(domain, healthy_proxies)
        elif self.rotation_strategy == "random":
            return random.choice(healthy_proxies)
        else:  # round_robin
            return self._get_round_robin_proxy(healthy_proxies)

    def _get_round_robin_proxy(self, healthy_proxies: list[Proxy]) -> Proxy:
        """Get next proxy in round-robin order."""
        # Find the next healthy proxy starting from current index
        for i in range(len(self.proxies)):
            idx = (self._current_index + i) % len(self.proxies)
            proxy = self.proxies[idx]
            if proxy.status == ProxyStatus.HEALTHY:
                self._current_index = (idx + 1) % len(self.proxies)
                return proxy

        # Fallback to first healthy (shouldn't reach here)
        return healthy_proxies[0]

    def _get_sticky_proxy(self, domain: str, healthy_proxies: list[Proxy]) -> Proxy:
        """Get same proxy for same domain (sticky session)."""
        if domain in self._domain_proxy_map:
            proxy = self._domain_proxy_map[domain]
            if proxy.status == ProxyStatus.HEALTHY:
                return proxy
            # Previous proxy unhealthy, assign new one
            del self._domain_proxy_map[domain]

        # Assign proxy based on domain hash for consistency
        idx = hash(domain) % len(healthy_proxies)
        proxy = healthy_proxies[idx]
        self._domain_proxy_map[domain] = proxy
        return proxy

    def mark_failed(self, proxy: Proxy, reason: str) -> None:
        """Mark proxy as failed and update health status.

        Args:
            proxy: The proxy that failed
            reason: Reason for failure
        """
        proxy.failure_count += 1
        proxy.last_failure_reason = reason

        if proxy.failure_count >= self.failure_threshold:
            proxy.status = ProxyStatus.UNHEALTHY
            logger.warning(
                "proxy_marked_unhealthy",
                proxy_url=proxy.url,
                failure_count=proxy.failure_count,
                reason=reason,
            )
        else:
            logger.debug(
                "proxy_failure_recorded",
                proxy_url=proxy.url,
                failure_count=proxy.failure_count,
                reason=reason,
            )

    def mark_success(self, proxy: Proxy) -> None:
        """Mark proxy as successful, resetting failure count.

        Args:
            proxy: The proxy that succeeded
        """
        proxy.failure_count = 0
        proxy.status = ProxyStatus.HEALTHY
        proxy.last_failure_reason = ""

    def get_health_stats(self) -> dict[str, int]:
        """Get health statistics for all proxies.

        Returns:
            dict with healthy, unhealthy, total counts
        """
        healthy = sum(1 for p in self.proxies if p.status == ProxyStatus.HEALTHY)
        unhealthy = sum(1 for p in self.proxies if p.status == ProxyStatus.UNHEALTHY)

        return {
            "healthy": healthy,
            "unhealthy": unhealthy,
            "total": len(self.proxies),
        }

    def reset_all(self) -> None:
        """Reset all proxies to healthy status."""
        for proxy in self.proxies:
            proxy.status = ProxyStatus.HEALTHY
            proxy.failure_count = 0
            proxy.last_failure_reason = ""

        self._domain_proxy_map.clear()
        logger.info("all_proxies_reset")
