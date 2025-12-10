"""Performance profiling utilities.

Provides middleware and utilities for tracking response times
and identifying performance bottlenecks.
"""

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


@dataclass
class RequestTiming:
    """Timing data for a single request."""

    path: str
    method: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    status_code: int = 200


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to capture request timing.

    Can be configured with a callback to receive timing data
    for logging, metrics collection, or alerting.
    """

    def __init__(
        self,
        app: Any,
        callback: Callable[[str, str, float], None] | None = None,
    ) -> None:
        """Initialize timing middleware.

        Args:
            app: The ASGI application.
            callback: Optional callback(path, method, duration_seconds).
        """
        super().__init__(app)
        self._callback = callback

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and capture timing.

        Args:
            request: The incoming request.
            call_next: Function to call next middleware/route.

        Returns:
            The response from the application.
        """
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # Still capture timing on errors
            duration = time.perf_counter() - start
            if self._callback:
                self._callback(request.url.path, request.method, duration)
            raise

        duration = time.perf_counter() - start

        if self._callback:
            self._callback(request.url.path, request.method, duration)

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration*1000:.2f}ms"

        return response


class PerformanceProfiler:
    """Collects and analyzes performance metrics.

    Use this class to track response times over time and
    identify slow endpoints or performance regressions.
    """

    def __init__(self, max_samples: int = 1000) -> None:
        """Initialize profiler.

        Args:
            max_samples: Maximum samples to keep per endpoint.
        """
        self._max_samples = max_samples
        self._timings: dict[str, list[RequestTiming]] = {}

    def record(self, timing: RequestTiming) -> None:
        """Record a timing measurement.

        Args:
            timing: The timing data to record.
        """
        key = f"{timing.method}:{timing.path}"
        if key not in self._timings:
            self._timings[key] = []

        self._timings[key].append(timing)

        # Trim if over limit
        if len(self._timings[key]) > self._max_samples:
            self._timings[key] = self._timings[key][-self._max_samples :]

    def get_stats(self, path: str, method: str = "GET") -> dict[str, float]:
        """Get statistics for an endpoint.

        Args:
            path: The endpoint path.
            method: The HTTP method.

        Returns:
            Dictionary with avg, min, max, p95, p99 in milliseconds.
        """
        key = f"{method}:{path}"
        timings = self._timings.get(key, [])

        if not timings:
            return {"avg": 0, "min": 0, "max": 0, "p95": 0, "p99": 0, "count": 0}

        durations = sorted(t.duration_ms for t in timings)
        count = len(durations)

        return {
            "avg": sum(durations) / count,
            "min": durations[0],
            "max": durations[-1],
            "p95": durations[int(count * 0.95)] if count > 1 else durations[0],
            "p99": durations[int(count * 0.99)] if count > 1 else durations[0],
            "count": count,
        }

    def get_slow_endpoints(self, threshold_ms: float = 100) -> list[dict[str, Any]]:
        """Get endpoints with average response time above threshold.

        Args:
            threshold_ms: Threshold in milliseconds.

        Returns:
            List of slow endpoints with their stats.
        """
        slow = []
        for key, timings in self._timings.items():
            if not timings:
                continue

            avg = sum(t.duration_ms for t in timings) / len(timings)
            if avg > threshold_ms:
                method, path = key.split(":", 1)
                slow.append(
                    {
                        "method": method,
                        "path": path,
                        "avg_ms": avg,
                        "count": len(timings),
                    }
                )

        return sorted(slow, key=lambda x: x["avg_ms"], reverse=True)

    def clear(self) -> None:
        """Clear all recorded timings."""
        self._timings.clear()


# Global profiler instance
_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get the global profiler instance.

    Returns:
        The global PerformanceProfiler.
    """
    return _profiler


def create_timing_callback() -> Callable[[str, str, float], None]:
    """Create a callback that records to the global profiler.

    Returns:
        A callback function for TimingMiddleware.
    """

    def callback(path: str, method: str, duration: float) -> None:
        """Record request timing to global profiler."""
        timing = RequestTiming(
            path=path,
            method=method,
            duration_ms=duration * 1000,
        )
        _profiler.record(timing)

    return callback
