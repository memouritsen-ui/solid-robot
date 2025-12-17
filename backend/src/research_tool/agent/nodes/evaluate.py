"""Evaluation node - calculate saturation metrics and determine if research should continue.

Phase 5 Enhancement:
- Tracks metrics across cycles for proper saturation detection
- Calculates growth rates to identify diminishing returns
- Detects circular citations
- Implements two-cycle confirmation before stopping
"""

from typing import Any

from research_tool.agent.decisions.saturation import calculate_saturation, should_stop
from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState

logger = get_logger(__name__)

# Maximum cycles before forced stop
MAX_CYCLES = 5

# Saturation threshold that must be exceeded for 2 consecutive cycles
SATURATION_THRESHOLD = 0.85


def _detect_circular_citations(facts: list[Any]) -> tuple[int, int]:
    """Detect circular citations among facts.

    A circular citation occurs when sources reference each other
    without adding new information.

    Args:
        facts: List of fact dictionaries with sources

    Returns:
        tuple[int, int]: (circular_count, total_count)
    """
    if not facts:
        return 0, 0

    # Filter to only dict facts (some tests pass non-dict values)
    dict_facts = [f for f in facts if isinstance(f, dict)]
    if not dict_facts:
        return 0, len(facts)

    # Build source -> fact mapping
    source_facts: dict[str, set[int]] = {}
    for i, fact in enumerate(dict_facts):
        for source in fact.get("sources", []):
            if source not in source_facts:
                source_facts[source] = set()
            source_facts[source].add(i)

    # Count facts that appear in multiple sources with same content
    # This is a simplified heuristic for circularity
    circular_count = 0
    seen_statements: dict[str, list[str]] = {}

    for fact in dict_facts:
        statement = fact.get("statement", "").lower().strip()
        sources = fact.get("sources", [])

        if statement in seen_statements:
            # Same statement from different sources could indicate circularity
            existing_sources = seen_statements[statement]
            if sources != existing_sources:
                circular_count += 1
        else:
            seen_statements[statement] = sources

    return circular_count, len(facts)


def _calculate_growth_rate(before: int, after: int) -> float:
    """Calculate growth rate between cycles.

    Args:
        before: Count before cycle
        after: Count after cycle

    Returns:
        Growth rate (0.0 to 1.0+, where 0.0 means no growth)
    """
    if before == 0:
        return 1.0 if after > 0 else 0.0
    return (after - before) / before


def _calculate_overall_saturation(
    entity_growth: float,
    fact_growth: float,
    new_sources: int
) -> float:
    """Calculate overall saturation score.

    Saturation = weighted average of:
    - Entity growth rate (inverted): 40%
    - Fact growth rate (inverted): 40%
    - Source exhaustion: 20%

    Args:
        entity_growth: Entity growth rate
        fact_growth: Fact growth rate
        new_sources: Number of new sources discovered

    Returns:
        Saturation score (0.0 to 1.0, where 1.0 = fully saturated)
    """
    # Invert growth rates (lower growth = higher saturation)
    entity_sat = 1.0 - min(entity_growth, 1.0)
    fact_sat = 1.0 - min(fact_growth, 1.0)
    source_sat = 1.0 if new_sources == 0 else 0.0

    return 0.4 * entity_sat + 0.4 * fact_sat + 0.2 * source_sat


async def evaluate_node(state: ResearchState) -> dict[str, Any]:
    """Evaluate research progress and calculate saturation metrics.

    Phase 5 Enhancement:
    - Properly tracks metrics across cycles
    - Implements two-cycle confirmation for stopping
    - Detects circular citations
    - Calculates growth rates

    Anti-pattern prevention:
    - Don't stop too early (Anti-Pattern #3) - requires 2 consecutive saturated cycles
    - Don't stop too late (Anti-Pattern #4) - max cycle limit

    Args:
        state: Current research state

    Returns:
        dict: State updates with saturation decision and cycle tracking
    """
    logger.info("evaluate_node_start")

    # Get current cycle (default to 1)
    current_cycle = state.get("current_cycle", 1)
    cycle_history = list(state.get("cycle_history", []))

    # Get current counts
    entities_current = len(state.get("entities_found", []))
    facts_current = len(state.get("facts_extracted", []))
    sources_current = len(state.get("sources_queried", []))
    facts_list = state.get("facts_extracted", [])

    # Get before counts from state (set during cycle start)
    entities_before = state.get("entities_before_cycle", 0)
    facts_before = state.get("facts_before_cycle", 0)

    # Detect circular citations
    circular_citations, total_citations = _detect_circular_citations(facts_list)

    # Estimate available sources (based on typical search results)
    # In production, this could come from search provider metadata
    sources_available = max(sources_current + 5, 10)

    # Calculate growth rates
    entity_growth = _calculate_growth_rate(entities_before, entities_current)
    fact_growth = _calculate_growth_rate(facts_before, facts_current)

    # Count new sources this cycle
    previous_sources = cycle_history[-1].get("sources_queried", 0) if cycle_history else 0
    new_sources = sources_current - previous_sources

    # Calculate overall saturation
    overall_saturation = _calculate_overall_saturation(
        entity_growth, fact_growth, new_sources
    )

    # Calculate standard saturation metrics
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

    # Build cycle record
    cycle_record = {
        "cycle": current_cycle,
        "entities_before": entities_before,
        "entities_after": entities_current,
        "entities_growth_rate": entity_growth,
        "facts_before": facts_before,
        "facts_after": facts_current,
        "facts_growth_rate": fact_growth,
        "new_sources_discovered": new_sources,
        "circular_citations_detected": circular_citations,
        "overall_saturation": overall_saturation,
        "sources_queried": sources_current,
        **metrics.to_dict()
    }

    # Add to history
    cycle_history.append(cycle_record)

    # Determine if we should stop
    stop = False
    reason = ""

    # Check max cycles
    if current_cycle >= MAX_CYCLES:
        stop = True
        reason = f"Maximum cycles reached ({MAX_CYCLES})"

    # Check saturation with two-cycle confirmation
    elif len(cycle_history) >= 2:
        last_two_saturations = [
            cycle_history[-1].get("overall_saturation", 0),
            cycle_history[-2].get("overall_saturation", 0)
        ]

        if all(s > SATURATION_THRESHOLD for s in last_two_saturations):
            stop = True
            reason = (
                f"Research saturated: {last_two_saturations[0]:.1%} and "
                f"{last_two_saturations[1]:.1%} saturation in last 2 cycles "
                f"(>{SATURATION_THRESHOLD:.0%} threshold)"
            )

    # Check standard saturation conditions if not already stopping
    if not stop:
        standard_stop, standard_reason = should_stop(metrics)
        if standard_stop and len(cycle_history) >= 2:
            # For standard conditions, still use two-cycle confirmation
            prev_metrics = cycle_history[-2]
            prev_sat = prev_metrics.get("overall_saturation", 0)
            if prev_sat > SATURATION_THRESHOLD:
                stop = True
                reason = standard_reason + " (confirmed over 2 cycles)"

    # Log with detailed metrics
    logger.info(
        "evaluate_node_complete",
        cycle=current_cycle,
        should_stop=stop,
        reason=reason if stop else "Continuing research",
        overall_saturation=overall_saturation,
        entity_growth=entity_growth,
        fact_growth=fact_growth,
        new_sources=new_sources
    )

    return {
        "saturation_metrics": metrics.to_dict(),
        "should_stop": stop,
        "stop_reason": reason if stop else None,
        "current_phase": "evaluate",
        "current_cycle": current_cycle + 1,  # Increment for next cycle
        "cycle_history": cycle_history,
        # Reset before counts for next cycle
        "entities_before_cycle": entities_current,
        "facts_before_cycle": facts_current
    }
