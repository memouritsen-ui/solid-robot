"""Library API endpoints for research session management.

Provides CRUD operations and full-text search for stored research sessions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from research_tool.core.logging import get_logger
from research_tool.services.memory.research_memory import (
    ResearchMemory,
    ResearchSession,
    init_research_memory,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/library", tags=["library"])

# Initialize memory on module load
_memory: ResearchMemory | None = None


def get_memory() -> ResearchMemory:
    """Get or initialize ResearchMemory instance."""
    global _memory
    if _memory is None:
        _memory = init_research_memory("./data/research_memory.db")
    return _memory


# --- Pydantic Models for API ---


class SessionListResponse(BaseModel):
    """Response model for session list."""

    sessions: list[SessionSummaryResponse]
    total: int
    offset: int
    limit: int


class SessionSummaryResponse(BaseModel):
    """Summary of a research session for list views."""

    session_id: str
    query: str
    domain: str
    status: str
    facts_count: int = 0
    sources_count: int = 0
    confidence_score: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class SessionDetailResponse(BaseModel):
    """Full detail of a research session."""

    session_id: str
    query: str
    domain: str
    privacy_mode: str
    status: str
    summary: str | None = None
    facts: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    confidence_score: float | None = None
    started_at: datetime
    completed_at: datetime | None = None
    saturation_metrics: dict[str, Any] | None = None


class SearchResultResponse(BaseModel):
    """Search result for a session."""

    session_id: str
    query: str
    summary: str | None = None
    started_at: datetime
    rank: float = 0.0


class SearchResponse(BaseModel):
    """Response model for search results."""

    results: list[SearchResultResponse]
    query: str
    total: int


class LibraryStatsResponse(BaseModel):
    """Response model for library statistics."""

    total_sessions: int = 0
    total_facts: int = 0
    total_sources: int = 0
    completed_sessions: int = 0
    average_confidence: float | None = None


class SaveSessionRequest(BaseModel):
    """Request model for saving a session."""

    session_id: str
    query: str
    domain: str = "general"
    privacy_mode: str = "cloud_allowed"
    status: str = "completed"
    summary: str | None = None
    facts: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    confidence_score: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    saturation_metrics: dict[str, Any] | None = None


# --- API Endpoints ---


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max sessions to return"),
) -> SessionListResponse:
    """List all research sessions with pagination.

    Args:
        offset: Number of sessions to skip
        limit: Maximum sessions to return

    Returns:
        Paginated list of session summaries
    """
    memory = get_memory()
    summaries = await memory.list_sessions(offset=offset, limit=limit)

    sessions = [
        SessionSummaryResponse(
            session_id=s.session_id,
            query=s.query,
            domain=s.domain,
            status=s.status,
            facts_count=s.facts_count,
            sources_count=s.sources_count,
            confidence_score=s.confidence_score,
            started_at=s.started_at,
            completed_at=s.completed_at,
        )
        for s in summaries
    ]

    # Get total count for pagination
    stats = await memory.get_statistics()

    return SessionListResponse(
        sessions=sessions,
        total=stats.total_sessions,
        offset=offset,
        limit=limit,
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str) -> SessionDetailResponse:
    """Get full details of a research session.

    Args:
        session_id: Session identifier

    Returns:
        Complete session with all data

    Raises:
        HTTPException: If session not found
    """
    memory = get_memory()
    session = await memory.get_session(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionDetailResponse(
        session_id=session.session_id,
        query=session.query,
        domain=session.domain,
        privacy_mode=session.privacy_mode,
        status=session.status,
        summary=session.summary,
        facts=session.facts,
        sources=session.sources,
        entities=session.entities,
        confidence_score=session.confidence_score,
        started_at=session.started_at,
        completed_at=session.completed_at,
        saturation_metrics=session.saturation_metrics,
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict[str, Any]:
    """Delete a research session.

    Args:
        session_id: Session to delete

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If session not found
    """
    memory = get_memory()
    deleted = await memory.delete_session(session_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    logger.info("session_deleted", session_id=session_id)

    return {
        "session_id": session_id,
        "status": "deleted",
        "message": "Session deleted successfully",
    }


@router.get("/search", response_model=SearchResponse)
async def search_sessions(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
) -> SearchResponse:
    """Search sessions using full-text search.

    Searches across queries, summaries, facts, and source titles.

    Args:
        q: Search query text
        limit: Maximum results to return

    Returns:
        List of matching sessions ranked by relevance
    """
    memory = get_memory()
    results = await memory.search_sessions(q, limit=limit)

    search_results = [
        SearchResultResponse(
            session_id=r.session_id,
            query=r.query,
            summary=r.summary,
            started_at=r.started_at,
            rank=r.rank,
        )
        for r in results
    ]

    return SearchResponse(
        results=search_results,
        query=q,
        total=len(search_results),
    )


@router.get("/stats", response_model=LibraryStatsResponse)
async def get_stats() -> LibraryStatsResponse:
    """Get library statistics.

    Returns:
        Aggregated statistics about the research library
    """
    memory = get_memory()
    stats = await memory.get_statistics()

    return LibraryStatsResponse(
        total_sessions=stats.total_sessions,
        total_facts=stats.total_facts,
        total_sources=stats.total_sources,
        completed_sessions=stats.completed_sessions,
        average_confidence=stats.average_confidence,
    )


@router.post("/sessions", response_model=dict[str, Any])
async def save_session(request: SaveSessionRequest) -> dict[str, Any]:
    """Save a research session to the library.

    Args:
        request: Session data to save

    Returns:
        Confirmation with session_id
    """
    memory = get_memory()

    session = ResearchSession(
        session_id=request.session_id,
        query=request.query,
        domain=request.domain,
        privacy_mode=request.privacy_mode,
        status=request.status,
        summary=request.summary,
        facts=request.facts,
        sources=request.sources,
        entities=request.entities,
        confidence_score=request.confidence_score,
        started_at=request.started_at or datetime.now(),
        completed_at=request.completed_at,
        saturation_metrics=request.saturation_metrics,
    )

    await memory.save_session(session)

    logger.info(
        "session_saved",
        session_id=request.session_id,
        facts_count=len(request.facts),
        sources_count=len(request.sources),
    )

    return {
        "session_id": request.session_id,
        "status": "saved",
        "message": "Session saved to library",
    }
