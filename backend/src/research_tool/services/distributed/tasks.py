"""Celery tasks for distributed crawling."""

import socket
from datetime import datetime, timezone
from typing import Any

from celery import Task

from research_tool.core.logging import get_logger
from research_tool.services.distributed.celery_app import app
from research_tool.services.distributed.config import DistributedConfig

logger = get_logger(__name__)
config = DistributedConfig()


def _fetch_url(url: str, options: dict) -> dict[str, Any]:
    """Fetch URL content using existing crawler logic.

    This is a sync wrapper that will be called by the Celery task.
    """
    import asyncio

    from research_tool.services.search.crawler import PlaywrightCrawler

    async def _async_fetch() -> dict[str, Any]:
        crawler = PlaywrightCrawler()
        result = await crawler.fetch_url(url)
        return result

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_async_fetch())
    finally:
        loop.close()


class CrawlTask(Task):
    """Base task with shared resources."""

    abstract = True


@app.task(
    bind=True,
    base=CrawlTask,
    max_retries=config.task_max_retries,
    rate_limit=config.task_rate_limit,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
)
def crawl_url(
    self: Task,
    url: str,
    session_id: str,
    options: dict | None = None,
) -> dict[str, Any]:
    """Crawl a single URL.

    Args:
        url: URL to crawl
        session_id: Research session ID for grouping
        options: Optional crawl options

    Returns:
        Dict with status, url, content, and metadata
    """
    options = options or {}
    worker_id = socket.gethostname()

    try:
        logger.info("crawl_task_start", url=url, session_id=session_id)

        result = _fetch_url(url, options)

        return {
            "status": "success",
            "url": url,
            "session_id": session_id,
            "worker_id": worker_id,
            "crawled_at": datetime.now(timezone.utc).isoformat(),
            **result,
        }

    except Exception as e:
        logger.error("crawl_task_error", url=url, error=str(e))
        return {
            "status": "failed",
            "url": url,
            "session_id": session_id,
            "worker_id": worker_id,
            "error": str(e),
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }
