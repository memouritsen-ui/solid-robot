"""Tests for CrawlCoordinator."""

from unittest.mock import MagicMock, patch

import pytest


class TestCrawlCoordinator:
    """Test CrawlCoordinator."""

    def test_coordinator_init(self) -> None:
        """Coordinator initializes with session_id."""
        from research_tool.services.distributed.coordinator import CrawlCoordinator

        coordinator = CrawlCoordinator(session_id="test-123")
        assert coordinator.session_id == "test-123"

    def test_get_stats_empty(self) -> None:
        """Stats returns zeros for empty results."""
        from research_tool.services.distributed.coordinator import CrawlCoordinator

        coordinator = CrawlCoordinator(session_id="test-123")
        stats = coordinator.get_stats([])

        assert stats["total"] == 0
        assert stats["success"] == 0
        assert stats["failed"] == 0

    def test_get_stats_with_results(self) -> None:
        """Stats correctly counts success/failure."""
        from research_tool.services.distributed.coordinator import CrawlCoordinator

        coordinator = CrawlCoordinator(session_id="test-123")
        results = [
            {"status": "success", "worker_id": "w1"},
            {"status": "success", "worker_id": "w2"},
            {"status": "failed", "worker_id": "w1"},
        ]
        stats = coordinator.get_stats(results)

        assert stats["total"] == 3
        assert stats["success"] == 2
        assert stats["failed"] == 1
        assert stats["workers_used"] == 2
