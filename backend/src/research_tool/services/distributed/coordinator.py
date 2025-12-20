"""Coordinator for distributed crawling."""

from collections.abc import Callable
from typing import Any

from celery import group
from celery.result import GroupResult

from research_tool.core.logging import get_logger
from research_tool.services.distributed.tasks import crawl_url

logger = get_logger(__name__)


class CrawlCoordinator:
    """Orchestrates distributed crawling and aggregates results."""

    def __init__(self, session_id: str):
        """Initialize coordinator.

        Args:
            session_id: Research session ID for grouping results
        """
        self.session_id = session_id

    def crawl_many_sync(
        self,
        urls: list[str],
        options: dict | None = None,
        timeout: float = 300.0,
    ) -> list[dict[str, Any]]:
        """Distribute URLs across workers and collect results (sync).

        Args:
            urls: List of URLs to crawl
            options: Optional crawl options
            timeout: Max wait time in seconds

        Returns:
            List of crawl results
        """
        if not urls:
            return []

        options = options or {}

        # Create task group
        task_group = group(
            crawl_url.s(url, self.session_id, options) for url in urls
        )

        # Execute
        logger.info(
            "distributed_crawl_start",
            session_id=self.session_id,
            url_count=len(urls),
        )

        group_result: GroupResult = task_group.apply_async()

        # Wait for results
        results = group_result.get(timeout=timeout, propagate=False)

        logger.info(
            "distributed_crawl_complete",
            session_id=self.session_id,
            result_count=len(results),
        )

        return results

    async def crawl_many(
        self,
        urls: list[str],
        options: dict | None = None,
        on_progress: Callable[[int, int], None] | None = None,
        timeout: float = 300.0,
    ) -> list[dict[str, Any]]:
        """Distribute URLs across workers and collect results (async).

        Args:
            urls: List of URLs to crawl
            options: Optional crawl options
            on_progress: Progress callback(completed, total)
            timeout: Max wait time in seconds

        Returns:
            List of crawl results
        """
        import asyncio

        if not urls:
            return []

        options = options or {}

        # Create and dispatch task group
        task_group = group(
            crawl_url.s(url, self.session_id, options) for url in urls
        )
        group_result: GroupResult = task_group.apply_async()

        # Poll for completion with progress updates
        completed = 0
        while not group_result.ready():
            new_completed = group_result.completed_count()
            if new_completed > completed:
                completed = new_completed
                if on_progress:
                    on_progress(completed, len(urls))
            await asyncio.sleep(0.5)

        # Final progress update
        if on_progress:
            on_progress(len(urls), len(urls))

        return group_result.get(timeout=timeout, propagate=False)

    def get_stats(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate statistics from results.

        Args:
            results: List of crawl results

        Returns:
            Stats dict with total, success, failed, workers_used
        """
        if not results:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "workers_used": 0,
            }

        success = sum(1 for r in results if r.get("status") == "success")
        workers = {r.get("worker_id") for r in results if r.get("worker_id")}

        return {
            "total": len(results),
            "success": success,
            "failed": len(results) - success,
            "workers_used": len(workers),
        }
