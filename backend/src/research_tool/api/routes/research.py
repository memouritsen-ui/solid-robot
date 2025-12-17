"""Research API endpoints."""

import traceback
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from research_tool.agent.graph import create_research_graph
from research_tool.core.logging import get_logger
from research_tool.models.requests import ResearchRequest, ResearchStatus

logger = get_logger(__name__)

router = APIRouter(prefix="/api/research", tags=["research"])

# Active research sessions (in-memory for now)
active_sessions: dict[str, dict[str, Any]] = {}


async def run_research_workflow(session_id: str, initial_state: dict[str, Any]) -> None:
    """Run research workflow in background.

    Args:
        session_id: Session identifier
        initial_state: Initial research state
    """
    try:
        logger.info("research_workflow_start", session_id=session_id)

        # Create graph
        logger.debug("creating_research_graph", session_id=session_id)
        graph = create_research_graph()
        logger.debug("graph_created", session_id=session_id)

        # Run workflow
        config = {"configurable": {"thread_id": session_id}}
        logger.info(
            "invoking_graph",
            session_id=session_id,
            state_keys=list(initial_state.keys())
        )

        final_state = await graph.ainvoke(initial_state, config=config)

        # Update session
        active_sessions[session_id]["state"] = final_state
        active_sessions[session_id]["status"] = "completed"

        logger.info(
            "research_workflow_complete",
            session_id=session_id,
            sources_queried=len(final_state.get("sources_queried", []))
        )

    except Exception as e:
        # Capture full traceback for debugging
        tb = traceback.format_exc()
        logger.error(
            "research_workflow_failed",
            session_id=session_id,
            error=str(e),
            error_type=type(e).__name__,
            traceback=tb
        )
        active_sessions[session_id]["status"] = "failed"
        active_sessions[session_id]["error"] = f"{type(e).__name__}: {str(e)}\n{tb}"


@router.post("/start")
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """Start a new research session.

    Args:
        request: Research request with query and settings
        background_tasks: FastAPI background tasks

    Returns:
        dict: Session info with session_id
    """
    session_id = str(uuid.uuid4())

    logger.info(
        "research_start_requested",
        session_id=session_id,
        query=request.query,
        privacy_mode=request.privacy_mode
    )

    # Initialize state
    initial_state = {
        "session_id": session_id,
        "original_query": request.query,
        "privacy_mode": request.privacy_mode,
        "started_at": datetime.now(),
        "current_phase": "starting",
        "sources_queried": [],
        "entities_found": [],
        "facts_extracted": [],
        "access_failures": [],
        "should_stop": False,
        "saturation_metrics": None,
        "stop_reason": None,
        "final_report": None,
        "export_path": None
    }

    # Store session
    active_sessions[session_id] = {
        "state": initial_state,
        "status": "running"
    }

    # Run in background
    background_tasks.add_task(run_research_workflow, session_id, initial_state)

    return {
        "session_id": session_id,
        "status": "started",
        "message": "Research workflow initiated"
    }


@router.get("/{session_id}/status")
async def get_research_status(session_id: str) -> ResearchStatus:
    """Get current status of a research session.

    Args:
        session_id: Session identifier

    Returns:
        ResearchStatus: Current status

    Raises:
        HTTPException: If session not found
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    state = session["state"]

    return ResearchStatus(
        session_id=session_id,
        status=session["status"],
        current_phase=state.get("current_phase"),
        sources_queried=len(state.get("sources_queried", [])),
        entities_found=len(state.get("entities_found", [])),
        facts_extracted=len(state.get("facts_extracted", [])),
        saturation_metrics=state.get("saturation_metrics"),
        stop_reason=state.get("stop_reason"),
        export_path=state.get("export_path")
    )


@router.post("/{session_id}/approve")
async def approve_research_plan(session_id: str) -> dict[str, Any]:
    """Approve research plan and allow agent to proceed.

    Used when agent requires explicit approval before continuing
    (e.g., after presenting research plan or clarification).

    Args:
        session_id: Session identifier

    Returns:
        dict: Approval confirmation

    Raises:
        HTTPException: If session not found or not waiting
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    state = session["state"]

    # Check if waiting for approval
    if not state.get("awaiting_approval", False):
        raise HTTPException(
            status_code=400,
            detail="Session not waiting for approval"
        )

    # Grant approval
    state["awaiting_approval"] = False
    state["approval_granted"] = True

    logger.info(
        "research_plan_approved",
        session_id=session_id,
        current_phase=state.get("current_phase")
    )

    return {
        "session_id": session_id,
        "status": "approved",
        "message": "Research approved, continuing workflow"
    }


@router.post("/{session_id}/stop")
async def stop_research(session_id: str) -> dict[str, Any]:
    """Stop a running research session early.

    Args:
        session_id: Session identifier

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException: If session not found
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]

    if session["status"] != "running":
        raise HTTPException(status_code=400, detail="Session not running")

    # Set stop flag
    session["state"]["should_stop"] = True
    session["state"]["stop_reason"] = "User requested stop"

    logger.info("research_stop_requested", session_id=session_id)

    return {
        "session_id": session_id,
        "status": "stopping",
        "message": "Stop signal sent to research workflow"
    }


@router.get("/{session_id}/report")
async def get_research_report(session_id: str) -> dict[str, Any]:
    """Get final research report.

    Args:
        session_id: Session identifier

    Returns:
        dict: Final research report

    Raises:
        HTTPException: If session not found or not completed
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]

    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Research not completed")

    final_report: dict[str, Any] | None = session["state"].get("final_report")

    if not final_report:
        raise HTTPException(status_code=404, detail="Report not generated")

    return final_report
