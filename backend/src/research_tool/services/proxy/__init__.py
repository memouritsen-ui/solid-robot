"""Proxy rotation system for anti-ban protection."""

from research_tool.services.proxy.manager import Proxy, ProxyManager, ProxyStatus
from research_tool.services.proxy.providers import (
    CompositeProxyProvider,
    EnvironmentProxyProvider,
    FileProxyProvider,
    ProxyProvider,
)

# Global proxy manager instance
_proxy_manager: ProxyManager | None = None


def get_proxy_manager() -> ProxyManager | None:
    """Get global proxy manager instance.

    Returns:
        ProxyManager if proxy is enabled, None otherwise
    """
    global _proxy_manager

    # Lazy initialization
    from research_tool.core.config import get_settings

    settings = get_settings()

    if not settings.proxy_enabled:
        return None

    if _proxy_manager is None:
        # Build proxy list from config
        proxies: list[str] = []

        # Load from comma-separated string
        if settings.proxy_list:
            proxies.extend(
                p.strip() for p in settings.proxy_list.split(",") if p.strip()
            )

        # Load from file
        if settings.proxy_file:
            file_provider = FileProxyProvider(settings.proxy_file)
            proxies.extend(file_provider.get_proxies())

        if proxies:
            _proxy_manager = ProxyManager(
                proxies=proxies,
                rotation_strategy=settings.proxy_rotation_strategy,
                failure_threshold=settings.proxy_failure_threshold,
            )

    return _proxy_manager


def reset_proxy_manager() -> None:
    """Reset the global proxy manager (for testing)."""
    global _proxy_manager
    _proxy_manager = None


__all__ = [
    "Proxy",
    "ProxyManager",
    "ProxyStatus",
    "ProxyProvider",
    "EnvironmentProxyProvider",
    "FileProxyProvider",
    "CompositeProxyProvider",
    "get_proxy_manager",
    "reset_proxy_manager",
]
