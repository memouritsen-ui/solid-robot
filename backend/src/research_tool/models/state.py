"""Research state for LangGraph workflow."""

from datetime import datetime
from operator import add
from typing import Annotated, Any

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
    entities_found: Annotated[list[dict[str, Any]], add]
    facts_extracted: Annotated[list[dict[str, Any]], add]
    access_failures: Annotated[list[dict[str, Any]], add]

    # URLs to crawl (optional)
    urls_to_crawl: list[str]

    # Current workflow state
    current_phase: str
    saturation_metrics: dict[str, Any] | None
    should_stop: bool
    stop_reason: str | None

    # Cycle tracking (Phase 5 enhancement)
    current_cycle: int
    cycle_history: list[dict[str, Any]]  # History of SaturationMetrics per cycle
    entities_before_cycle: int  # Entity count at start of current cycle
    facts_before_cycle: int  # Fact count at start of current cycle

    # Output
    final_report: dict[str, Any] | None
    export_path: str | None
