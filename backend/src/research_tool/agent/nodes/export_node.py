"""Export node - prepare final report for export."""

from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState
from research_tool.services.memory import CombinedMemoryRepository
from research_tool.services.memory.learning import PostResearchLearner, SourceLearning

logger = get_logger(__name__)


async def _trigger_learning(state: ResearchState) -> dict[str, Any]:
    """Trigger post-research learning to update source effectiveness.

    Args:
        state: Research state with sources_queried, facts_extracted, etc.

    Returns:
        dict: Learning summary with sources_updated count
    """
    sources_queried = list(state.get("sources_queried", []))
    if not sources_queried:
        return {"sources_updated": 0}

    try:
        # Initialize memory and learning components
        memory = CombinedMemoryRepository()
        await memory.initialize()
        source_learning = SourceLearning(memory.sqlite)
        learner = PostResearchLearner(source_learning)

        # Build research result for learning
        research_result = {
            "domain": state.get("domain", "general"),
            "sources_queried": sources_queried,
            "facts_extracted": list(state.get("facts_extracted", [])),
            "access_failures": list(state.get("access_failures", [])),
        }

        return await learner.trigger_learning(research_result)

    except Exception as e:
        logger.error("learning_trigger_error", error=str(e))
        return {"sources_updated": 0, "error": str(e)}


async def export_node(state: ResearchState) -> dict[str, Any]:
    """Prepare final research report for export.

    This node marks the research as ready for export and triggers
    post-research learning to update source effectiveness scores.

    Args:
        state: Current research state with final_report

    Returns:
        dict: State updates marking export readiness
    """
    logger.info("export_node_start")

    final_report = state.get("final_report")

    if not final_report:
        logger.warning("export_node_no_report", message="No final report found")
        return {
            "export_ready": False,
            "export_error": "No report to export",
            "current_phase": "export",
            "learning_summary": {"sources_updated": 0},
        }

    # Trigger learning to update source effectiveness (#226)
    learning_summary = await _trigger_learning(state)

    logger.info(
        "export_node_complete",
        report_ready=True,
        sources=final_report.get("sources_queried", 0),
        sources_learned=learning_summary.get("sources_updated", 0),
    )

    return {
        "export_ready": True,
        "export_formats_available": ["json", "markdown"],  # Placeholder for Phase 6
        "current_phase": "export",
        "learning_summary": learning_summary,
    }
