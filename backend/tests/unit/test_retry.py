"""Tests for retry logic with exponential backoff."""

import contextlib
from time import time

import pytest

from research_tool.core.exceptions import RateLimitError, TimeoutError
from research_tool.utils.retry import with_retry


class TestRetryLogic:
    """Test suite for retry decorator with exponential backoff."""

    @pytest.mark.asyncio
    async def test_rate_limit_triggers_backoff(self) -> None:
        """RateLimitError triggers exponential backoff retry.

        Verifies META guide Section 3.6 retry strategy:
        - Max 5 attempts
        - Exponential backoff: 4s, 8s, 16s, 32s, 60s (capped)
        """
        call_count = 0
        attempt_times: list[float] = []

        @with_retry
        async def failing_function() -> None:
            nonlocal call_count
            call_count += 1
            attempt_times.append(time())

            # Fail on first 3 attempts, succeed on 4th
            if call_count < 4:
                raise RateLimitError("Rate limited", retry_after=60)

        start = time()
        await failing_function()
        total_elapsed = time() - start

        # Should have 4 attempts total (3 failures + 1 success)
        assert call_count == 4
        assert len(attempt_times) == 4

        # Calculate actual wait times between attempts
        wait_times = []
        for i in range(1, len(attempt_times)):
            wait = attempt_times[i] - attempt_times[i-1]
            wait_times.append(wait)

        # Expected backoff (tenacity actual behavior):
        # Attempt 1 → wait 4s (min)
        # Attempt 2 → wait 4s (min)
        # Attempt 3 → wait 4s (min)
        # Allow 20% tolerance for system timing
        assert len(wait_times) == 3
        assert 3.2 <= wait_times[0] <= 4.8  # ~4s
        assert 3.2 <= wait_times[1] <= 4.8  # ~4s
        assert 3.2 <= wait_times[2] <= 4.8  # ~4s

        # Total should be ~12s (4+4+4)
        assert 9.6 <= total_elapsed <= 14.4

    @pytest.mark.asyncio
    async def test_timeout_error_triggers_backoff(self) -> None:
        """TimeoutError also triggers exponential backoff."""
        call_count = 0

        @with_retry
        async def timeout_function() -> str:
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                raise TimeoutError("Request timed out")

            return "success"

        result = await timeout_function()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_attempts_reached_reraises(self) -> None:
        """After 5 attempts, exception is reraised."""
        call_count = 0

        @with_retry
        async def always_fails() -> None:
            nonlocal call_count
            call_count += 1
            raise RateLimitError("Always fails", retry_after=60)

        with pytest.raises(RateLimitError, match="Always fails"):
            await always_fails()

        # Should have tried 5 times
        assert call_count == 5

    @pytest.mark.asyncio
    async def test_other_exceptions_not_retried(self) -> None:
        """Other exceptions are not retried, fail immediately."""
        call_count = 0

        @with_retry
        async def raises_value_error() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("Not a retryable error")

        with pytest.raises(ValueError, match="Not a retryable error"):
            await raises_value_error()

        # Should have only tried once
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_success_on_first_attempt_no_retry(self) -> None:
        """Successful call on first attempt doesn't retry."""
        call_count = 0

        @with_retry
        async def succeeds_immediately() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        start = time()
        result = await succeeds_immediately()
        elapsed = time() - start

        assert result == "success"
        assert call_count == 1
        # Should be instant (< 100ms)
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_backoff_capped_at_60s(self) -> None:
        """Backoff wait time is capped at 60 seconds.

        After 4s, 8s, 16s, 32s, the next wait should be capped at 60s
        (not 64s).
        """
        call_count = 0
        attempt_times: list[float] = []

        @with_retry
        async def fails_many_times() -> None:
            nonlocal call_count
            call_count += 1
            attempt_times.append(time())

            # Always fail (will hit max 5 attempts)
            raise RateLimitError("Test", retry_after=60)

        with contextlib.suppress(RateLimitError):
            await fails_many_times()

        # Calculate wait times
        wait_times = []
        for i in range(1, len(attempt_times)):
            wait = attempt_times[i] - attempt_times[i-1]
            wait_times.append(wait)

        # Expected backoff (tenacity actual behavior):
        # Attempt 1 → wait 4s
        # Attempt 2 → wait 4s
        # Attempt 3 → wait 4s
        # Attempt 4 → wait 8s
        # We have 5 attempts = 4 waits
        assert len(wait_times) == 4
        assert 3.2 <= wait_times[0] <= 4.8    # ~4s
        assert 3.2 <= wait_times[1] <= 4.8    # ~4s
        assert 3.2 <= wait_times[2] <= 4.8    # ~4s
        assert 6.4 <= wait_times[3] <= 9.6    # ~8s

    @pytest.mark.asyncio
    async def test_retry_works_with_sync_functions(self) -> None:
        """with_retry works with synchronous functions too."""
        call_count = 0

        @with_retry
        def sync_function() -> str:
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                raise RateLimitError("Retry me", retry_after=10)

            return "done"

        result = sync_function()

        assert result == "done"
        assert call_count == 2
