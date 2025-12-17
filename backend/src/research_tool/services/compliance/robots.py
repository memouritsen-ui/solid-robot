"""robots.txt parser and compliance checker."""

import re
from urllib.parse import urlparse

import httpx

from research_tool.core.logging import get_logger
from research_tool.services.compliance.cache import RobotsCache

logger = get_logger(__name__)


class RobotsChecker:
    """Parse and enforce robots.txt rules."""

    def __init__(
        self,
        user_agent: str = "SolidRobotBot/1.0",
        allow_on_error: bool = True,
        cache_ttl: int = 86400,
    ):
        """Initialize robots checker.

        Args:
            user_agent: User-agent to check rules for
            allow_on_error: Allow access if robots.txt fetch fails
            cache_ttl: Cache TTL in seconds
        """
        self.user_agent = user_agent
        self.allow_on_error = allow_on_error
        self._cache = RobotsCache(ttl_seconds=cache_ttl)

    async def can_fetch(self, url: str, user_agent: str | None = None) -> bool:
        """Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check
            user_agent: Override user-agent for this check (optional)

        Returns:
            True if allowed, False if disallowed
        """
        effective_agent = user_agent or self.user_agent
        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            path = parsed.path or "/"

            robots_content = await self._get_robots(domain)

            if robots_content is None:
                return True  # No robots.txt = allow all

            return self._check_rules(robots_content, path, effective_agent)

        except Exception as e:
            logger.warning(
                "robots_check_error",
                url=url,
                error=str(e),
            )
            return self.allow_on_error

    async def get_crawl_delay(self, url: str) -> float | None:
        """Get crawl-delay from robots.txt.

        Args:
            url: URL to get delay for

        Returns:
            Crawl delay in seconds or None
        """
        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"

            robots_content = await self._get_robots(domain)

            if robots_content is None:
                return None

            return self._extract_crawl_delay(robots_content)

        except Exception as e:
            logger.warning(
                "crawl_delay_error",
                url=url,
                error=str(e),
            )
            return None

    async def get_sitemap_urls(self, url: str) -> list[str]:
        """Get sitemap URLs from robots.txt.

        Args:
            url: URL to get sitemaps for

        Returns:
            List of sitemap URLs
        """
        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"

            robots_content = await self._get_robots(domain)

            if robots_content is None:
                return []

            return self._extract_sitemaps(robots_content)

        except Exception as e:
            logger.warning(
                "sitemap_extraction_error",
                url=url,
                error=str(e),
            )
            return []

    async def _get_robots(self, domain: str) -> str | None:
        """Get robots.txt content (cached).

        Args:
            domain: Domain URL (scheme + netloc)

        Returns:
            robots.txt content or None
        """
        # Check cache first
        cached = self._cache.get(domain)
        if cached is not None:
            return cached

        # Fetch robots.txt
        content = await self._fetch_robots(domain)

        if content is not None:
            self._cache.set(domain, content)

        return content

    async def _fetch_robots(self, domain: str) -> str | None:
        """Fetch robots.txt from domain.

        Args:
            domain: Domain URL

        Returns:
            robots.txt content or None if not found
        """
        robots_url = f"{domain}/robots.txt"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(robots_url)

                if response.status_code == 200:
                    logger.debug("robots_fetched", domain=domain)
                    return response.text
                elif response.status_code == 404:
                    logger.debug("robots_not_found", domain=domain)
                    return None
                else:
                    logger.warning(
                        "robots_fetch_failed",
                        domain=domain,
                        status=response.status_code,
                    )
                    return None

        except Exception as e:
            logger.warning(
                "robots_fetch_error",
                domain=domain,
                error=str(e),
            )
            raise

    def _check_rules(self, content: str, path: str, user_agent: str | None = None) -> bool:
        """Check if path is allowed by robots.txt rules.

        Args:
            content: robots.txt content
            path: Path to check
            user_agent: User-agent to check rules for

        Returns:
            True if allowed, False if disallowed
        """
        effective_agent = user_agent or self.user_agent
        lines = content.split("\n")
        current_agent = None
        rules_for_agent: list[tuple[str, bool]] = []  # (pattern, is_allow)
        rules_for_all: list[tuple[str, bool]] = []

        for line in lines:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse directive
            if ":" not in line:
                continue

            directive, value = line.split(":", 1)
            directive = directive.strip().lower()
            value = value.strip()

            if directive == "user-agent":
                current_agent = value.lower()
            elif directive in ("allow", "disallow") and value:
                is_allow = directive == "allow"
                pattern = self._pattern_to_regex(value)

                if current_agent == effective_agent.lower() or (
                    current_agent and effective_agent.lower().startswith(current_agent.rstrip("*"))
                ):
                    rules_for_agent.append((pattern, is_allow))
                elif current_agent == "*":
                    rules_for_all.append((pattern, is_allow))

        # Use agent-specific rules if available, otherwise use * rules
        rules = rules_for_agent if rules_for_agent else rules_for_all

        # Check rules in order (first match wins)
        for pattern, is_allow in rules:
            if re.match(pattern, path):
                return is_allow

        # Default: allow
        return True

    def _pattern_to_regex(self, pattern: str) -> str:
        """Convert robots.txt pattern to regex.

        Args:
            pattern: robots.txt pattern

        Returns:
            Regex pattern
        """
        # Escape special chars except * and $
        escaped = re.escape(pattern)

        # Convert * to .*
        escaped = escaped.replace(r"\*", ".*")

        # Handle $ at end (exact match)
        if escaped.endswith(r"\$"):
            escaped = escaped[:-2] + "$"
        else:
            # Match any continuation
            escaped = escaped + ".*"

        return "^" + escaped

    def _extract_crawl_delay(self, content: str) -> float | None:
        """Extract crawl-delay from robots.txt.

        Args:
            content: robots.txt content

        Returns:
            Crawl delay in seconds or None
        """
        lines = content.split("\n")
        current_agent = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" not in line:
                continue

            directive, value = line.split(":", 1)
            directive = directive.strip().lower()
            value = value.strip()

            if directive == "user-agent":
                current_agent = value.lower()
            elif directive == "crawl-delay":
                if current_agent == "*" or current_agent == self.user_agent.lower():
                    try:
                        return float(value)
                    except ValueError:
                        pass

        return None

    def _extract_sitemaps(self, content: str) -> list[str]:
        """Extract sitemap URLs from robots.txt.

        Args:
            content: robots.txt content

        Returns:
            List of sitemap URLs
        """
        sitemaps: list[str] = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" not in line:
                continue

            directive, value = line.split(":", 1)
            directive = directive.strip().lower()
            value = value.strip()

            if directive == "sitemap":
                sitemaps.append(value)

        return sitemaps

    def clear_cache(self, domain: str | None = None) -> None:
        """Clear robots.txt cache.

        Args:
            domain: Specific domain to clear, or None for all
        """
        self._cache.clear(domain)
