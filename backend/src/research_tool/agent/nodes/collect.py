"""Collection node - query sources per plan and crawl full content."""

from contextlib import suppress
from datetime import datetime

from research_tool.core.logging import get_logger
from research_tool.models.domain import DomainConfiguration
from research_tool.models.state import ResearchState
from research_tool.services.search.arxiv import ArxivProvider
from research_tool.services.search.brave import BraveProvider
from research_tool.services.search.crawler import PlaywrightCrawler
from research_tool.services.search.pubmed import PubMedProvider
from research_tool.services.search.semantic_scholar import SemanticScholarProvider
from research_tool.services.search.tavily import TavilyProvider

logger = get_logger(__name__)

# Global crawler instance (reuse browser across calls)
_crawler: PlaywrightCrawler | None = None


def get_crawler() -> PlaywrightCrawler:
    """Get or create the global crawler instance."""
    global _crawler
    if _crawler is None:
        _crawler = PlaywrightCrawler(headless=True, timeout_ms=30000)
    return _crawler


async def collect_node(state: ResearchState) -> dict:
    """Collect data from sources per research plan.

    This node:
    1. Queries search providers (Tavily, Brave, Scholar, etc.)
    2. Uses Playwright crawler to fetch full content for top results
    3. Returns enriched results with full_content populated

    Anti-pattern prevention:
    - Use ranked sources (Anti-Pattern #5)
    - Handle obstacles gracefully (Anti-Pattern #6)

    Args:
        state: Current research state

    Returns:
        dict: State updates with new sources queried and enriched entities
    """
    logger.info("collect_node_start")

    refined_query = state.get("refined_query", state["original_query"])
    domain = state.get("domain", "general")

    # Get domain configuration
    if domain == "medical":
        config = DomainConfiguration.for_medical()
    elif domain == "competitive_intelligence":
        config = DomainConfiguration.for_competitive_intelligence()
    elif domain == "academic":
        config = DomainConfiguration.for_academic()
    elif domain == "regulatory":
        config = DomainConfiguration.for_regulatory()
    else:
        config = DomainConfiguration.default()

    # Initialize providers
    providers = {}
    with suppress(ValueError):  # Not configured
        providers["tavily"] = TavilyProvider()

    providers["semantic_scholar"] = SemanticScholarProvider()
    providers["pubmed"] = PubMedProvider()
    providers["arxiv"] = ArxivProvider()

    with suppress(ValueError):  # Not configured
        providers["brave"] = BraveProvider()

    # Query primary sources first
    sources_queried = []
    all_results = []

    for source_name in config.primary_sources:
        if source_name in providers:
            provider = providers[source_name]
            if await provider.is_available():
                try:
                    results = await provider.search(refined_query, max_results=10)
                    sources_queried.append(source_name)
                    all_results.extend(results)
                    logger.info(
                        "source_queried",
                        source=source_name,
                        results_count=len(results)
                    )
                except Exception as e:
                    logger.error(
                        "source_query_failed",
                        source=source_name,
                        error=str(e)
                    )

    # Query secondary sources if needed
    for source_name in config.secondary_sources:
        if source_name in providers and len(all_results) < 10:
            provider = providers[source_name]
            if await provider.is_available():
                try:
                    results = await provider.search(refined_query, max_results=5)
                    sources_queried.append(source_name)
                    all_results.extend(results)
                    logger.info(
                        "secondary_source_queried",
                        source=source_name,
                        results_count=len(results)
                    )
                except Exception as e:
                    logger.error(
                        "secondary_source_failed",
                        source=source_name,
                        error=str(e)
                    )

    logger.info(
        "initial_search_complete",
        sources_queried=len(sources_queried),
        total_results=len(all_results)
    )

    # Use Playwright crawler to enrich top results with full content
    enriched_results = all_results
    crawler = get_crawler()

    if await crawler.is_available():
        try:
            # Crawl top 10 results that don't already have full content
            results_to_crawl = [
                r for r in all_results[:15]
                if not r.get("full_content") or len(r.get("full_content", "")) < 500
            ]

            if results_to_crawl:
                logger.info(
                    "crawler_enrichment_start",
                    results_to_crawl=len(results_to_crawl)
                )

                enriched_results = await crawler.crawl_search_results(
                    all_results,
                    max_crawl=10
                )

                # Count how many were actually enriched
                crawled_count = sum(1 for r in enriched_results if r.get("crawled"))
                logger.info(
                    "crawler_enrichment_complete",
                    crawled_count=crawled_count,
                    total_results=len(enriched_results)
                )

                if crawled_count > 0:
                    sources_queried.append("playwright_crawler")

        except Exception as e:
            logger.error("crawler_enrichment_failed", error=str(e))
            # Continue with non-enriched results
            enriched_results = all_results
    else:
        logger.warning("crawler_not_available_skipping_enrichment")

    # Convert results to entities with full content
    entities_found = []
    for result in enriched_results[:20]:  # Limit for state size
        entity = {
            "url": result.get("url"),
            "title": result.get("title"),
            "snippet": result.get("snippet", ""),
            "source": result.get("source_name"),
            "retrieved_at": datetime.now().isoformat(),
            "has_full_content": bool(result.get("full_content")),
        }

        # Include full content if available
        if result.get("full_content"):
            entity["full_content"] = result["full_content"]
            entity["content_length"] = len(result["full_content"])

        # Include metadata
        if result.get("metadata"):
            entity["metadata"] = result["metadata"]

        entities_found.append(entity)

    logger.info(
        "collect_node_complete",
        sources_queried=len(sources_queried),
        entities_found=len(entities_found),
        with_full_content=sum(1 for e in entities_found if e.get("has_full_content"))
    )

    return {
        "sources_queried": sources_queried,
        "entities_found": entities_found,
        "current_phase": "collect"
    }


async def crawl_urls_node(state: ResearchState) -> dict:
    """Dedicated node for crawling specific URLs.

    Use this when you have a list of URLs to crawl directly,
    rather than searching first.

    Args:
        state: Current research state with 'urls_to_crawl' list

    Returns:
        dict: State updates with crawled entities
    """
    urls = state.get("urls_to_crawl", [])

    if not urls:
        logger.info("crawl_urls_no_urls")
        return {"entities_found": [], "current_phase": "crawl_urls"}

    crawler = get_crawler()

    if not await crawler.is_available():
        logger.error("crawl_urls_crawler_not_available")
        return {"entities_found": [], "current_phase": "crawl_urls"}

    logger.info("crawl_urls_start", url_count=len(urls))

    entities_found = []
    for url in urls:
        try:
            page_data = await crawler.fetch_page(url)

            if page_data.get("content"):
                entities_found.append({
                    "url": url,
                    "title": page_data.get("title", ""),
                    "snippet": (page_data["content"][:500] + "...")
                        if len(page_data["content"]) > 500
                        else page_data["content"],
                    "full_content": page_data["content"],
                    "source": "playwright_crawler",
                    "retrieved_at": datetime.now().isoformat(),
                    "has_full_content": True,
                    "content_length": len(page_data["content"]),
                    "metadata": page_data.get("metadata", {})
                })
                logger.info("crawl_url_success", url=url)
            else:
                logger.warning("crawl_url_no_content", url=url)

        except Exception as e:
            logger.error("crawl_url_failed", url=url, error=str(e))

    logger.info(
        "crawl_urls_complete",
        total_urls=len(urls),
        successful=len(entities_found)
    )

    return {
        "entities_found": entities_found,
        "sources_queried": ["playwright_crawler"] if entities_found else [],
        "current_phase": "crawl_urls"
    }
