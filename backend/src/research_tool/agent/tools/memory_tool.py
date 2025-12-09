"""Memory tool for LangGraph agent."""

from typing import Any

from research_tool.core.logging import get_logger
from research_tool.services.memory.repository import MemoryRepository

logger = get_logger(__name__)


async def search_memory(
    query: str,
    memory_repo: MemoryRepository,
    max_results: int = 5
) -> dict[str, Any]:
    """Search memory for similar documents.

    LangGraph tool wrapper for memory retrieval functionality.

    Args:
        query: Search query
        memory_repo: Memory repository instance
        max_results: Maximum number of results to return

    Returns:
        dict: Memory search results with metadata
    """
    logger.info(
        "memory_tool_search_start",
        query=query,
        max_results=max_results
    )

    try:
        # Search for similar documents
        similar_docs = await memory_repo.search_similar(
            query=query,
            limit=max_results
        )

        results = [
            {
                "content": doc.get("content", ""),
                "source": doc.get("source", ""),
                "url": doc.get("url", ""),
                "timestamp": doc.get("timestamp"),
                "similarity_score": doc.get("similarity_score", 0.0)
            }
            for doc in similar_docs
        ]

        logger.info(
            "memory_tool_search_complete",
            result_count=len(results)
        )

        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }

    except Exception as e:
        logger.error(
            "memory_tool_search_failed",
            error=str(e)
        )
        return {
            "query": query,
            "results": [],
            "total_found": 0,
            "error": str(e)
        }


async def get_source_effectiveness(
    memory_repo: MemoryRepository
) -> dict[str, Any]:
    """Get source effectiveness scores from memory.

    LangGraph tool wrapper for source effectiveness retrieval.
    Note: Gets all sources (repository interface requires source_name parameter).

    Args:
        memory_repo: Memory repository instance

    Returns:
        dict: Source effectiveness scores
    """
    logger.info("memory_tool_effectiveness_start")

    try:
        # Get effectiveness for a default/all sources
        # Repository requires source_name, so we use a placeholder
        # Phase 5 will enhance this with proper source listing
        effectiveness_scores: dict[str, float] = {}

        # For now, return empty dict as placeholder
        # Full implementation in Phase 5 when repository is enhanced
        logger.info(
            "memory_tool_effectiveness_complete",
            source_count=len(effectiveness_scores)
        )

        return {
            "effectiveness_scores": effectiveness_scores
        }

    except Exception as e:
        logger.error(
            "memory_tool_effectiveness_failed",
            error=str(e)
        )
        return {
            "effectiveness_scores": {},
            "error": str(e)
        }
