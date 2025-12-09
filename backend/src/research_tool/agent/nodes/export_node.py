"""Export node - prepare final report for export."""

from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState

logger = get_logger(__name__)


async def export_node(state: ResearchState) -> dict[str, Any]:
    """Prepare final research report for export.

    This node marks the research as ready for export. Actual export
    functionality (PDF, DOCX, etc.) will be implemented in Phase 6.

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
            "current_phase": "export"
        }

    # Mark report as ready for export
    # Phase 6 will implement actual export formats (PDF, DOCX, MD, etc.)
    logger.info(
        "export_node_complete",
        report_ready=True,
        sources=final_report.get("sources_queried", 0)
    )

    return {
        "export_ready": True,
        "export_formats_available": ["json", "markdown"],  # Placeholder for Phase 6
        "current_phase": "export"
    }
