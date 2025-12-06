"""API request and response models."""

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    """Request to start a new research session."""

    query: str = Field(..., min_length=3, max_length=500, description="Research query")
    privacy_mode: str = Field(
        default="CLOUD_ALLOWED",
        description="Privacy mode: LOCAL_ONLY, CLOUD_ALLOWED, or HYBRID"
    )
    domain: str | None = Field(
        default=None,
        description="Optional domain hint (medical, academic, competitive_intelligence, etc.)"
    )
    max_sources: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of sources to query"
    )


class ResearchStatus(BaseModel):
    """Status of an ongoing or completed research session."""

    session_id: str
    status: str  # "running", "completed", "failed", "stopped"
    current_phase: str | None = None
    sources_queried: int = 0
    entities_found: int = 0
    facts_extracted: int = 0
    saturation_metrics: dict | None = None
    stop_reason: str | None = None
    export_path: str | None = None


class ProgressUpdate(BaseModel):
    """Progress update for WebSocket streaming."""

    type: str  # "progress", "complete", "error"
    phase: str | None = None
    message: str | None = None
    sources_queried: int = 0
    entities_found: int = 0
    facts_extracted: int = 0
    data: dict | None = None
