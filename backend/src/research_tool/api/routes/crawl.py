"""Crawl API endpoints for distributed and local crawling."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from research_tool.core.logging import get_logger
from research_tool.services.distributed import CrawlCoordinator, is_distributed_available
from research_tool.services.search.crawler import PlaywrightCrawler

logger = get_logger(__name__)

router = APIRouter(prefix="/api/crawl", tags=["crawl"])


class BatchCrawlRequest(BaseModel):
    """Request for batch crawl operation."""

    urls: list[str] = Field(..., description="URLs to crawl")
    distributed: bool = Field(default=False, description="Use distributed crawling")
    options: dict[str, Any] = Field(default_factory=dict, description="Crawl options")
    timeout: float = Field(default=300.0, description="Timeout in seconds")


class BatchCrawlResponse(BaseModel):
    """Response from batch crawl operation."""

    session_id: str
    results: list[dict[str, Any]]
    stats: dict[str, Any] | None = None
    distributed: bool


@router.post("/batch", response_model=BatchCrawlResponse)
async def batch_crawl(request: BatchCrawlRequest) -> BatchCrawlResponse:
    """Crawl multiple URLs in batch.

    Args:
        request: Batch crawl request with URLs and options

    Returns:
        BatchCrawlResponse with results and stats
    """
    session_id = str(uuid.uuid4())

    logger.info(
        "batch_crawl_start",
        session_id=session_id,
        url_count=len(request.urls),
        distributed=request.distributed,
    )

    if not request.urls:
        return BatchCrawlResponse(
            session_id=session_id,
            results=[],
            stats=None,
            distributed=request.distributed,
        )

    if request.distributed:
        # Check if distributed is available
        if not is_distributed_available():
            raise HTTPException(
                status_code=503,
                detail="Distributed crawling unavailable (Redis not connected)",
            )

        # Use coordinator for distributed crawling
        coordinator = CrawlCoordinator(session_id=session_id)
        results = coordinator.crawl_many_sync(
            urls=request.urls,
            options=request.options,
            timeout=request.timeout,
        )
        stats = coordinator.get_stats(results)

        return BatchCrawlResponse(
            session_id=session_id,
            results=results,
            stats=stats,
            distributed=True,
        )

    else:
        # Local crawling with PlaywrightCrawler
        crawler = PlaywrightCrawler()
        results = []

        try:
            for url in request.urls:
                try:
                    result = await crawler.fetch_page(url)
                    results.append({"status": "success", "url": url, **result})
                except Exception as e:
                    logger.error("local_crawl_error", url=url, error=str(e))
                    results.append({"status": "failed", "url": url, "error": str(e)})
        finally:
            await crawler.close()

        return BatchCrawlResponse(
            session_id=session_id,
            results=results,
            stats=None,
            distributed=False,
        )


@router.get("/distributed/status")
async def distributed_status() -> dict[str, Any]:
    """Check if distributed crawling is available.

    Returns:
        Status of distributed crawling infrastructure
    """
    available = is_distributed_available()

    return {
        "distributed_available": available,
        "message": "Redis connected" if available else "Redis not available",
    }
