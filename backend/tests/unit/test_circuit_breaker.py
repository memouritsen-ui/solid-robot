"""Tests for circuit breaker pattern."""

from datetime import datetime, timedelta
from unittest.mock import patch

from research_tool.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    get_circuit_breaker,
)


class TestCircuitBreaker:
    """Test suite for CircuitBreaker class."""

    def test_init_starts_closed(self) -> None:
        """CircuitBreaker initializes in CLOSED state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.failures == 0
        assert cb.last_failure is None

    def test_init_accepts_custom_thresholds(self) -> None:
        """CircuitBreaker accepts custom threshold and timeout."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30

    def test_can_execute_when_closed(self) -> None:
        """can_execute returns True when circuit is CLOSED."""
        cb = CircuitBreaker()
        assert cb.can_execute() is True

    def test_record_failure_increments_count(self) -> None:
        """record_failure increments failure count."""
        cb = CircuitBreaker()
        cb.record_failure()
        assert cb.failures == 1
        assert cb.last_failure is not None

    def test_circuit_opens_after_threshold_failures(self) -> None:
        """Circuit opens after reaching failure threshold."""
        cb = CircuitBreaker(failure_threshold=3)

        # Record failures below threshold
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        # Record failure at threshold
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.failures == 3

    def test_can_execute_blocks_when_open(self) -> None:
        """can_execute returns False when circuit is OPEN."""
        cb = CircuitBreaker(failure_threshold=2)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Should block execution
        assert cb.can_execute() is False

    def test_circuit_transitions_to_half_open_after_timeout(self) -> None:
        """Circuit transitions to HALF_OPEN after recovery timeout."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=5)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Mock time to simulate timeout elapsed
        future_time = datetime.now() + timedelta(seconds=10)
        with patch("research_tool.utils.circuit_breaker.datetime") as mock_datetime:
            mock_datetime.now.return_value = future_time
            # Keep original last_failure
            cb.last_failure = datetime.now()

            # After timeout, should transition to HALF_OPEN
            result = cb.can_execute()
            assert result is True
            assert cb.state == CircuitState.HALF_OPEN

    def test_can_execute_allows_one_request_in_half_open(self) -> None:
        """can_execute allows requests in HALF_OPEN state."""
        cb = CircuitBreaker()
        cb.state = CircuitState.HALF_OPEN

        assert cb.can_execute() is True

    def test_record_success_closes_circuit(self) -> None:
        """record_success closes the circuit and resets failures."""
        cb = CircuitBreaker(failure_threshold=2)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Record success - should close and reset
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failures == 0

    def test_record_success_from_half_open_closes_circuit(self) -> None:
        """record_success from HALF_OPEN closes the circuit."""
        cb = CircuitBreaker()
        cb.state = CircuitState.HALF_OPEN
        cb.failures = 5

        cb.record_success()

        assert cb.state == CircuitState.CLOSED
        assert cb.failures == 0

    def test_reset_manually_closes_circuit(self) -> None:
        """reset() manually closes the circuit."""
        cb = CircuitBreaker(failure_threshold=2)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Manual reset
        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.failures == 0
        assert cb.last_failure is None

    def test_multiple_failures_while_open_stay_open(self) -> None:
        """Recording failures while OPEN keeps circuit OPEN."""
        cb = CircuitBreaker(failure_threshold=2)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # More failures shouldn't change state
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.failures == 4

    def test_circuit_stays_open_before_timeout(self) -> None:
        """Circuit stays OPEN before recovery timeout elapsed."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Immediately check - should still be blocked
        assert cb.can_execute() is False
        assert cb.state == CircuitState.OPEN


class TestGetCircuitBreaker:
    """Test suite for get_circuit_breaker factory function."""

    def test_get_circuit_breaker_creates_new_instance(self) -> None:
        """get_circuit_breaker creates new instance for new service."""
        cb = get_circuit_breaker("test_service")
        assert cb is not None
        assert isinstance(cb, CircuitBreaker)

    def test_get_circuit_breaker_returns_same_instance(self) -> None:
        """get_circuit_breaker returns same instance for same service."""
        cb1 = get_circuit_breaker("same_service")
        cb2 = get_circuit_breaker("same_service")

        assert cb1 is cb2

    def test_get_circuit_breaker_different_services_independent(self) -> None:
        """Different services get independent circuit breakers."""
        cb_service_a = get_circuit_breaker("service_a")
        cb_service_b = get_circuit_breaker("service_b")

        # Fail service_a
        cb_service_a.record_failure()
        cb_service_a.record_failure()
        cb_service_a.record_failure()
        cb_service_a.record_failure()
        cb_service_a.record_failure()

        # service_a should be open
        assert cb_service_a.state == CircuitState.OPEN

        # service_b should still be closed
        assert cb_service_b.state == CircuitState.CLOSED


class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker pattern."""

    def test_typical_failure_recovery_cycle(self) -> None:
        """Test complete failure → open → half-open → closed cycle."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

        # Step 1: Normal operation (CLOSED)
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True

        # Step 2: Failures accumulate
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED  # Still below threshold

        # Step 3: Circuit opens
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False  # Blocked

        # Step 4: Wait for recovery timeout
        future_time = datetime.now() + timedelta(seconds=10)
        with patch("research_tool.utils.circuit_breaker.datetime") as mock_datetime:
            mock_datetime.now.return_value = future_time
            cb.last_failure = datetime.now()

            # Should transition to HALF_OPEN
            assert cb.can_execute() is True
            assert cb.state == CircuitState.HALF_OPEN

        # Step 5: Recovery (success closes circuit)
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failures == 0

    def test_half_open_failure_reopens_circuit(self) -> None:
        """Failure in HALF_OPEN state reopens the circuit."""
        cb = CircuitBreaker(failure_threshold=3)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Transition to HALF_OPEN
        cb.state = CircuitState.HALF_OPEN

        # Failure in HALF_OPEN
        cb.record_failure()

        # Should stay/reopen as OPEN
        assert cb.state == CircuitState.OPEN
        assert cb.failures == 4
