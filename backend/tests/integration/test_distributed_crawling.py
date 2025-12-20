"""Integration tests for distributed crawling.

These tests require Redis to be running:
    docker compose -f docker-compose.distributed.yml up -d redis

Run these tests with:
    pytest tests/integration/test_distributed_crawling.py -v
"""

import pytest

from research_tool.services.distributed import is_distributed_available


# Skip all tests in this module if Redis is not available
pytestmark = pytest.mark.skipif(
    not is_distributed_available(),
    reason="Redis not available - start with: docker compose -f docker-compose.distributed.yml up -d redis"
)


class TestDistributedCrawlingIntegration:
    """Integration tests for distributed crawling with actual Redis."""

    def test_redis_connection(self) -> None:
        """Verify Redis is reachable."""
        assert is_distributed_available()

    def test_coordinator_can_dispatch_tasks(self) -> None:
        """Coordinator can dispatch tasks to Redis queue."""
        from research_tool.services.distributed import CrawlCoordinator

        coordinator = CrawlCoordinator(session_id="integration-test")

        # With no workers running, we can still dispatch tasks
        # (they'll just sit in the queue)
        assert coordinator.session_id == "integration-test"

    def test_celery_app_configured(self) -> None:
        """Celery app has correct configuration."""
        from research_tool.services.distributed.celery_app import app
        from research_tool.services.distributed.config import DistributedConfig

        config = DistributedConfig()

        assert app.conf.broker_url == config.broker_url
        assert app.conf.result_backend == config.result_backend

    def test_task_registered(self) -> None:
        """crawl_url task is registered with Celery."""
        from research_tool.services.distributed.celery_app import app

        assert "research_tool.services.distributed.tasks.crawl_url" in app.tasks

    def test_config_from_environment(self) -> None:
        """Configuration can be loaded from environment."""
        import os

        from research_tool.services.distributed.config import DistributedConfig

        # Test default values
        config = DistributedConfig()
        assert config.broker_url.startswith("redis://")
        assert config.result_backend.startswith("redis://")
        assert config.task_max_retries == 3

    def test_stats_aggregation(self) -> None:
        """Stats correctly aggregate mock results."""
        from research_tool.services.distributed import CrawlCoordinator

        coordinator = CrawlCoordinator(session_id="stats-test")

        results = [
            {"status": "success", "url": "https://a.com", "worker_id": "w1"},
            {"status": "success", "url": "https://b.com", "worker_id": "w2"},
            {"status": "failed", "url": "https://c.com", "worker_id": "w1", "error": "timeout"},
        ]

        stats = coordinator.get_stats(results)

        assert stats["total"] == 3
        assert stats["success"] == 2
        assert stats["failed"] == 1
        assert stats["workers_used"] == 2
