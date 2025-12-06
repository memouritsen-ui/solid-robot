"""Circuit breaker to prevent cascade failures."""

from datetime import datetime, timedelta
from enum import Enum

from research_tool.core.logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Failing, reject requests
    HALF_OPEN = "half_open"    # Testing recovery


class CircuitBreaker:
    """Prevent cascade failures by breaking the circuit after threshold failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject all requests
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before testing recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure: datetime | None = None

    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self.failures += 1
        self.last_failure = datetime.now()

        if self.failures >= self.failure_threshold and self.state != CircuitState.OPEN:
            logger.warning(
                "circuit_breaker_opened",
                failures=self.failures,
                threshold=self.failure_threshold
            )
            self.state = CircuitState.OPEN

    def record_success(self) -> None:
        """Record a success and close the circuit."""
        if self.state != CircuitState.CLOSED:
            logger.info("circuit_breaker_closed", previous_failures=self.failures)

        self.failures = 0
        self.state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        """Check if a request can be executed.

        Returns:
            bool: True if request should be attempted
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if we should try recovery
            if self.last_failure and datetime.now() - self.last_failure > timedelta(
                seconds=self.recovery_timeout
            ):
                logger.info("circuit_breaker_half_open", testing_recovery=True)
                self.state = CircuitState.HALF_OPEN
                return True

            logger.debug("circuit_breaker_blocking", state="open")
            return False

        # HALF_OPEN - allow one request to test
        return True

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        logger.info("circuit_breaker_reset", previous_failures=self.failures)
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure = None


# Global circuit breakers per service
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(service: str) -> CircuitBreaker:
    """Get or create circuit breaker for a service.

    Args:
        service: Service name

    Returns:
        CircuitBreaker: Circuit breaker instance for the service
    """
    if service not in _circuit_breakers:
        _circuit_breakers[service] = CircuitBreaker()
    return _circuit_breakers[service]
