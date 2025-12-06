"""Retry logic with exponential backoff."""

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from research_tool.core.exceptions import RateLimitError, TimeoutError
from research_tool.core.logging import get_logger

logger = get_logger(__name__)


def with_retry(func):
    """Decorator for retry with exponential backoff.

    Retry strategy from META guide Section 3.6:
    - Max 5 attempts
    - Exponential backoff: 4s, 8s, 16s, 32s, 60s (capped)
    - Only retry on RateLimitError and TimeoutError

    Usage:
        @with_retry
        async def fetch_data():
            ...
    """
    return retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((RateLimitError, TimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            "retry_attempt",
            attempt=retry_state.attempt_number,
            wait_seconds=retry_state.next_action.sleep if retry_state.next_action else 0,
            exception=str(retry_state.outcome.exception()) if retry_state.outcome else None
        ),
        reraise=True
    )(func)
