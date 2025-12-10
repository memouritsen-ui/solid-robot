"""Export node - prepare final report for export."""

from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState
from research_tool.services.memory import CombinedMemoryRepository
from research_tool.services.memory.learning import PostResearchLearner, SourceLearning

logger = get_logger(__name__)


async def _trigger_learning(state: ResearchState) -> dict[str, Any]:
    """Trigger post-research learning to update source effectiveness.

    Also updates domain config based on discovered sources (#227).

    Args:
        state: Research state with sources_queried, facts_extracted, etc.

    Returns:
        dict: Learning summary with sources_updated count and domain_config_updated flag
    """
    sources_queried = list(state.get("sources_queried", []))
    if not sources_queried:
        return {"sources_updated": 0, "domain_config_updated": False}

    try:
        # Initialize memory and learning components
        memory = CombinedMemoryRepository()
        await memory.initialize()
        source_learning = SourceLearning(memory.sqlite)
        learner = PostResearchLearner(source_learning)

        # Build research result for learning
        domain = state.get("domain", "general")
        facts_extracted = list(state.get("facts_extracted", []))
        access_failures = list(state.get("access_failures", []))

        research_result = {
            "domain": domain,
            "sources_queried": sources_queried,
            "facts_extracted": facts_extracted,
            "access_failures": access_failures,
        }

        learning_summary = await learner.trigger_learning(research_result)

        # #227: Update domain config based on discovered sources
        domain_config_updated = await _update_domain_config(
            memory.sqlite, domain, sources_queried, facts_extracted, access_failures
        )
        learning_summary["domain_config_updated"] = domain_config_updated

        return learning_summary

    except Exception as e:
        logger.error("learning_trigger_error", error=str(e))
        return {"sources_updated": 0, "domain_config_updated": False, "error": str(e)}


async def _update_domain_config(
    sqlite_repo: Any,
    domain: str,
    sources_queried: list[str],
    facts_extracted: list[dict[str, Any]],
    access_failures: list[dict[str, Any]],
) -> bool:
    """Update domain configuration based on research results.

    #227: Update domain config based on discovered sources.

    - Sources with high avg confidence -> preferred_sources
    - Sources with permanent failures -> excluded_sources

    Args:
        sqlite_repo: SQLite repository for persistence
        domain: Domain name
        sources_queried: List of sources used
        facts_extracted: List of extracted facts with source and confidence
        access_failures: List of access failures

    Returns:
        bool: True if config was updated
    """
    if not sources_queried:
        return False

    # Calculate average confidence per source
    source_confidences: dict[str, list[float]] = {}
    for fact in facts_extracted:
        source = fact.get("source", "").lower()
        confidence = fact.get("confidence", 0.5)
        if source:
            if source not in source_confidences:
                source_confidences[source] = []
            source_confidences[source].append(confidence)

    # Find high-performing sources (avg confidence > 0.75)
    preferred_sources = []
    for source, confidences in source_confidences.items():
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            if avg_confidence > 0.75:
                preferred_sources.append(source)

    # Find failed sources
    excluded_sources = [
        f.get("source", "").lower()
        for f in access_failures
        if f.get("source")
    ]

    # Only update if we have something to update
    if not preferred_sources and not excluded_sources:
        return False

    # Update domain config in database
    await sqlite_repo.update_domain_config(
        domain=domain,
        preferred_sources=preferred_sources if preferred_sources else None,
        excluded_sources=excluded_sources if excluded_sources else None,
    )

    logger.info(
        "domain_config_updated",
        domain=domain,
        preferred_sources=preferred_sources,
        excluded_sources=excluded_sources,
    )

    return True


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
