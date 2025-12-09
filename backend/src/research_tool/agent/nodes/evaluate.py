"""Evaluation node - calculate saturation metrics and determine if research should continue."""

from typing import Any

from research_tool.agent.decisions.saturation import calculate_saturation, should_stop
from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState

logger = get_logger(__name__)


async def evaluate_node(state: ResearchState) -> dict[str, Any]:
    """Evaluate research progress and calculate saturation metrics.

    Anti-pattern prevention:
    - Don't stop too early (Anti-Pattern #3)
    - Don't stop too late (Anti-Pattern #4)

    Args:
        state: Current research state

    Returns:
        dict: State updates with saturation decision
    """
    logger.info("evaluate_node_start")

    # Get current counts
    entities_current = len(state.get("entities_found", []))
    facts_current = len(state.get("facts_extracted", []))
    sources_current = len(state.get("sources_queried", []))

    # For first cycle, assume 0 before
    # In full implementation, this would track across cycles
    entities_before = 0
    facts_before = 0

    # Placeholder values for circularity
    circular_citations = 0
    total_citations = max(facts_current, 1)

    # Available sources (simplified)
    sources_available = 10

    # Calculate saturation
    metrics = calculate_saturation(
        entities_before=entities_before,
        entities_after=entities_current,
        facts_before=facts_before,
        facts_after=facts_current,
        circular_citations=circular_citations,
        total_citations=total_citations,
        sources_queried=sources_current,
        sources_available=sources_available
    )

    # Determine if we should stop
    stop, reason = should_stop(metrics)

    logger.info(
        "evaluate_node_complete",
        should_stop=stop,
        reason=reason,
        metrics=metrics.to_dict()
    )

    return {
        "saturation_metrics": metrics.to_dict(),
        "should_stop": stop,
        "stop_reason": reason if stop else None,
        "current_phase": "evaluate"
    }
