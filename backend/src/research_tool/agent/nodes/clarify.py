"""Clarification node - analyze query and ask if genuinely needed."""

from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState

logger = get_logger(__name__)


async def clarify_node(state: ResearchState) -> dict[str, Any]:
    """Clarify the research query if needed.

    Anti-pattern prevention: MAX 2 clarification exchanges (Anti-Pattern #1, #2)

    Args:
        state: Current research state

    Returns:
        dict: State updates
    """
    logger.info("clarify_node_start", query=state["original_query"])

    # For now, use original query as refined query
    # In full implementation, this would:
    # 1. Analyze query for ambiguity
    # 2. Ask user only if genuinely blocked (MAX 2 exchanges)
    # 3. Detect domain from query

    refined_query = state.get("refined_query") or state["original_query"]

    # Simple domain detection (placeholder for full implementation)
    query_lower = refined_query.lower()
    domain = "general"

    if any(kw in query_lower for kw in ["medical", "disease", "treatment", "patient", "clinical"]):
        domain = "medical"
    elif any(kw in query_lower for kw in ["company", "market", "competitor", "startup"]):
        domain = "competitive_intelligence"
    elif any(kw in query_lower for kw in ["research", "paper", "study", "academic"]):
        domain = "academic"
    elif any(kw in query_lower for kw in ["regulation", "compliance", "law", "policy"]):
        domain = "regulatory"

    logger.info("clarify_node_complete", domain=domain, refined_query=refined_query)

    return {
        "refined_query": refined_query,
        "domain": domain,
        "current_phase": "clarify"
    }
