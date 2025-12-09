"""Search tool for LangGraph agent."""

from typing import Any

from research_tool.core.logging import get_logger
from research_tool.services.search.provider import SearchProvider

logger = get_logger(__name__)


async def search_sources(
    query: str,
    sources: list[str],
    provider_registry: dict[str, SearchProvider]
) -> dict[str, Any]:
    """Search multiple sources for a query.

    LangGraph tool wrapper for search functionality.
    Phase 4: Simple wrapper, Phase 5 will add parallel execution.

    Args:
        query: Search query
        sources: List of source names to query
        provider_registry: Registry of available search providers

    Returns:
        dict: Search results with metadata
    """
    logger.info(
        "search_tool_start",
        query=query,
        sources=sources
    )

    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for source_name in sources:
        provider = provider_registry.get(source_name)

        if not provider:
            logger.warning(
                "search_tool_provider_not_found",
                source=source_name
            )
            errors.append({
                "source": source_name,
                "error": "Provider not found in registry"
            })
            continue

        try:
            # Execute search
            source_results = await provider.search(query, max_results=10)

            results.extend([
                {
                    "source": source_name,
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "relevance_score": result.get("relevance_score", 0.0),
                    "published_date": result.get("published_date")
                }
                for result in source_results
            ])

            logger.info(
                "search_tool_source_complete",
                source=source_name,
                result_count=len(source_results)
            )

        except Exception as e:
            logger.error(
                "search_tool_source_failed",
                source=source_name,
                error=str(e)
            )
            errors.append({
                "source": source_name,
                "error": str(e)
            })

    logger.info(
        "search_tool_complete",
        total_results=len(results),
        total_errors=len(errors)
    )

    return {
        "query": query,
        "results": results,
        "errors": errors,
        "sources_queried": len(sources),
        "sources_succeeded": len(sources) - len(errors)
    }
