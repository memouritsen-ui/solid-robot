"""Synthesis node - generate final research report."""

from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState

logger = get_logger(__name__)


async def synthesize_node(state: ResearchState) -> dict[str, Any]:
    """Synthesize research findings into final report.

    Anti-pattern prevention:
    - Include what was NOT found (Anti-Pattern #11)
    - Explain stopping rationale (Anti-Pattern #12)

    Args:
        state: Current research state

    Returns:
        dict: State updates with final report
    """
    logger.info("synthesize_node_start")

    # Generate report
    report = {
        "query": state.get("refined_query", state["original_query"]),
        "domain": state.get("domain"),
        "sources_queried": len(state.get("sources_queried", [])),
        "sources_list": state.get("sources_queried", []),
        "entities_found": len(state.get("entities_found", [])),
        "facts_extracted": len(state.get("facts_extracted", [])),
        "saturation_metrics": state.get("saturation_metrics"),
        "stop_reason": state.get("stop_reason"),
        "summary": f"Research completed for: {state.get('refined_query', state['original_query'])}",
        "findings": state.get("facts_extracted", [])[:20],  # Top facts
        "limitations": [
            "This is a preliminary report",
            "Full text analysis not yet implemented",
            "Cross-verification simplified"
        ]
    }

    logger.info(
        "synthesize_node_complete",
        sources=report["sources_queried"],
        entities=report["entities_found"]
    )

    return {
        "final_report": report,
        "current_phase": "synthesize"
    }
