"""Proxy providers for loading proxy lists from various sources."""

import os
from abc import ABC, abstractmethod
from pathlib import Path

from research_tool.core.logging import get_logger

logger = get_logger(__name__)


class ProxyProvider(ABC):
    """Abstract base class for proxy providers."""

    @abstractmethod
    def get_proxies(self) -> list[str]:
        """Get list of proxy URLs.

        Returns:
            List of proxy URL strings
        """
        pass


class EnvironmentProxyProvider(ProxyProvider):
    """Load proxies from environment variable."""

    def __init__(self, env_var: str = "PROXY_LIST"):
        """Initialize with environment variable name.

        Args:
            env_var: Name of environment variable containing proxies
        """
        self.env_var = env_var

    def get_proxies(self) -> list[str]:
        """Get proxies from comma-separated environment variable.

        Returns:
            List of proxy URLs
        """
        proxy_string = os.environ.get(self.env_var, "")

        if not proxy_string:
            return []

        proxies = [p.strip() for p in proxy_string.split(",") if p.strip()]

        logger.info(
            "proxies_loaded_from_env",
            env_var=self.env_var,
            count=len(proxies),
        )

        return proxies


class FileProxyProvider(ProxyProvider):
    """Load proxies from a file."""

    def __init__(self, file_path: str):
        """Initialize with file path.

        Args:
            file_path: Path to proxy file
        """
        self.file_path = file_path

    def get_proxies(self) -> list[str]:
        """Get proxies from file (one per line).

        Returns:
            List of proxy URLs
        """
        path = Path(self.file_path)

        if not path.exists():
            logger.warning(
                "proxy_file_not_found",
                file_path=self.file_path,
            )
            return []

        try:
            content = path.read_text()
            lines = content.strip().split("\n")

            # Filter empty lines and comments
            proxies = [
                line.strip()
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]

            logger.info(
                "proxies_loaded_from_file",
                file_path=self.file_path,
                count=len(proxies),
            )

            return proxies

        except Exception as e:
            logger.error(
                "proxy_file_read_error",
                file_path=self.file_path,
                error=str(e),
            )
            return []


class CompositeProxyProvider(ProxyProvider):
    """Combine multiple proxy providers."""

    def __init__(self, providers: list[ProxyProvider]):
        """Initialize with list of providers.

        Args:
            providers: List of proxy providers to combine
        """
        self.providers = providers

    def get_proxies(self) -> list[str]:
        """Get proxies from all providers.

        Returns:
            Combined list of unique proxy URLs
        """
        all_proxies: list[str] = []

        for provider in self.providers:
            proxies = provider.get_proxies()
            all_proxies.extend(proxies)

        # Remove duplicates while preserving order
        seen: set[str] = set()
        unique_proxies: list[str] = []
        for proxy in all_proxies:
            if proxy not in seen:
                seen.add(proxy)
                unique_proxies.append(proxy)

        return unique_proxies
