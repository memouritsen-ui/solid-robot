"""Obstacle handling decision tree from META guide Section 7.4."""

from research_tool.core.exceptions import AccessDeniedError, RateLimitError, TimeoutError
from research_tool.core.logging import get_logger
from research_tool.services.memory import MemoryRepository

logger = get_logger(__name__)


class ObstacleHandler:
    """Handle research obstacles per decision tree.

    Decision tree from META guide:
    - Rate limit → exponential backoff → retry
    - Access denied → record failure → try next source
    - Timeout → retry with longer timeout (max 3)
    - Unknown error → log and skip
    """

    def __init__(self, memory: MemoryRepository) -> None:
        """Initialize obstacle handler.

        Args:
            memory: Memory repository for recording failures
        """
        self.memory = memory
        self.timeout_retries: dict[str, int] = {}

    async def handle(
        self,
        error: Exception,
        source_name: str,
        url: str
    ) -> str:
        """Handle obstacle and return action.

        Args:
            error: The exception that occurred
            source_name: Name of the source that failed
            url: URL that failed

        Returns:
            str: Action to take - "retry", "skip", "fallback", "abort"
        """
        if isinstance(error, RateLimitError):
            # Decision tree: rate_limit → exponential backoff → retry
            logger.info(
                "obstacle_rate_limit",
                source=source_name,
                retry_after=error.retry_after
            )
            return "retry"

        elif isinstance(error, AccessDeniedError):
            # Decision tree: access_denied → record failure → try next source
            logger.warning(
                "obstacle_access_denied",
                source=source_name,
                url=url
            )
            await self.memory.record_access_failure(
                url=url,
                source_name=source_name,
                error_type="access_denied",
                error_message=str(error)
            )
            return "skip"

        elif isinstance(error, TimeoutError):
            # Decision tree: timeout → retry with longer timeout (max 3)
            retry_key = f"{source_name}:{url}"
            retries = self.timeout_retries.get(retry_key, 0)

            if retries < 3:
                self.timeout_retries[retry_key] = retries + 1
                logger.info(
                    "obstacle_timeout_retry",
                    source=source_name,
                    url=url,
                    attempt=retries + 1
                )
                return "retry"
            else:
                logger.warning(
                    "obstacle_timeout_exhausted",
                    source=source_name,
                    url=url,
                    max_retries=3
                )
                await self.memory.record_access_failure(
                    url=url,
                    source_name=source_name,
                    error_type="timeout",
                    error_message=f"Timeout after {retries} retries"
                )
                return "skip"

        else:
            # Unknown error
            logger.error(
                "obstacle_unknown",
                source=source_name,
                url=url,
                error_type=type(error).__name__,
                error_message=str(error)
            )
            return "skip"

    def reset_timeout_counters(self) -> None:
        """Reset timeout retry counters (e.g., between research cycles)."""
        self.timeout_retries.clear()
