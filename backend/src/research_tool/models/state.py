"""Research state for LangGraph workflow."""

from datetime import datetime
from operator import add
from typing import Annotated

from typing_extensions import TypedDict


class ResearchState(TypedDict, total=False):
    """State maintained throughout research workflow.

    Uses TypedDict with LangGraph's Annotated pattern for accumulation.
    """

    # Immutable inputs
    session_id: str
    original_query: str
    privacy_mode: str  # "LOCAL_ONLY", "CLOUD_ALLOWED", "HYBRID"
    started_at: datetime

    # Refined during clarification
    refined_query: str
    domain: str

    # Accumulating lists (use Annotated with add operator for LangGraph)
    sources_queried: Annotated[list[str], add]
    entities_found: Annotated[list[dict], add]
    facts_extracted: Annotated[list[dict], add]
    access_failures: Annotated[list[dict], add]

    # Current workflow state
    current_phase: str
    saturation_metrics: dict | None
    should_stop: bool
    stop_reason: str | None

    # Output
    final_report: dict | None
    export_path: str | None
