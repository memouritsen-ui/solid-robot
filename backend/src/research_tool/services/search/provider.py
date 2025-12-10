"""Search provider abstract interface with circuit breaker and retry integration."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from research_tool.core.logging import get_logger
from research_tool.utils.circuit_breaker import get_circuit_breaker

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def with_circuit_breaker(provider_name: str) -> Callable[[F], F]:
    """Decorator to wrap provider methods with circuit breaker.

    Args:
        provider_name: Name of the provider for circuit breaker lookup

    Returns:
        Decorated function with circuit breaker protection
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cb = get_circuit_breaker(provider_name)

            if not cb.can_execute():
                logger.warning(
                    "circuit_breaker_blocked",
                    provider=provider_name,
                    state=cb.state.value
                )
                return []  # Return empty results when circuit is open

            try:
                result = await func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                logger.error(
                    "provider_error_recorded",
                    provider=provider_name,
                    error=str(e),
                    failures=cb.failures
                )
                raise

        return wrapper  # type: ignore
    return decorator


class SearchProvider(ABC):
    """Abstract interface for search providers with built-in resilience."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this provider."""
        pass

    @property
    @abstractmethod
    def requests_per_second(self) -> float:
        """Rate limit for this provider (requests per second)."""
        pass

    @abstractmethod
    async def _do_search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Internal search implementation - override this in subclasses.

        Args:
            query: The search query
            max_results: Maximum number of results to return
            filters: Optional filters (provider-specific)

        Returns:
            list[dict]: List of result dictionaries
        """
        pass

    async def search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute search with circuit breaker and retry protection.

        This method wraps _do_search with:
        1. Circuit breaker to prevent cascade failures
        2. Logging of all operations

        Args:
            query: The search query
            max_results: Maximum number of results to return
            filters: Optional filters (provider-specific)

        Returns:
            list[dict]: List of result dictionaries with keys:
                - url: Result URL
                - title: Result title
                - snippet: Result snippet/abstract
                - source_name: Name of this provider
                - full_content: Optional full text content
                - metadata: Optional provider-specific metadata
        """
        cb = get_circuit_breaker(self.name)

        if not cb.can_execute():
            logger.warning(
                "search_blocked_circuit_open",
                provider=self.name,
                state=cb.state.value
            )
            return []

        try:
            logger.info(
                "search_start",
                provider=self.name,
                query=query[:50],
                max_results=max_results
            )

            results = await self._do_search(query, max_results, filters)

            cb.record_success()

            logger.info(
                "search_complete",
                provider=self.name,
                results_count=len(results)
            )

            return results

        except Exception as e:
            cb.record_failure()
            logger.error(
                "search_failed",
                provider=self.name,
                error=str(e),
                circuit_failures=cb.failures
            )
            raise

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is configured and accessible.

        Returns:
            bool: True if provider can be used
        """
        pass

    def get_circuit_status(self) -> dict[str, Any]:
        """Get current circuit breaker status for this provider.

        Returns:
            dict with circuit breaker state and failure count
        """
        cb = get_circuit_breaker(self.name)
        return {
            "state": cb.state.value,
            "failures": cb.failures,
            "failure_threshold": cb.failure_threshold
        }
