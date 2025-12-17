"""Compliance services for ethical scraping."""

from research_tool.services.compliance.cache import RobotsCache
from research_tool.services.compliance.robots import RobotsChecker

# Global robots checker instance
_robots_checker: RobotsChecker | None = None


def get_robots_checker() -> RobotsChecker:
    """Get global robots checker instance.

    Returns:
        RobotsChecker instance
    """
    global _robots_checker

    if _robots_checker is None:
        from research_tool.core.config import get_settings

        settings = get_settings()

        _robots_checker = RobotsChecker(
            user_agent=settings.robots_user_agent,
            allow_on_error=settings.robots_allow_on_error,
            cache_ttl=settings.robots_cache_ttl,
        )

    return _robots_checker


def reset_robots_checker() -> None:
    """Reset global robots checker (for testing)."""
    global _robots_checker
    _robots_checker = None


__all__ = [
    "RobotsCache",
    "RobotsChecker",
    "get_robots_checker",
    "reset_robots_checker",
]
