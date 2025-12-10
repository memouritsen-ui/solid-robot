"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from research_tool.api.routes import export, health, research
from research_tool.api.websocket import chat_websocket, progress_handler
from research_tool.core import Settings, get_logger
from research_tool.utils.profiling import (
    TimingMiddleware,
    create_timing_callback,
    get_profiler,
)

settings = Settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events.

    Args:
        app: FastAPI application instance.

    Yields:
        Nothing, but handles startup and shutdown.
    """
    # Startup
    logger.info("application_starting", host=settings.host, port=settings.port)
    yield
    # Shutdown
    logger.info("application_shutting_down")


app = FastAPI(
    title="Research Tool API",
    version="0.1.0",
    description="Professional research assistant backend",
    lifespan=lifespan,
)

# CORS for SwiftUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Performance timing middleware
app.add_middleware(TimingMiddleware, callback=create_timing_callback())

# Include routers
app.include_router(health.router)
app.include_router(research.router)
app.include_router(export.router)


# Note: /api/health endpoints are now in health.router


@app.get("/api/metrics/performance")
async def performance_metrics() -> dict[str, Any]:
    """Get performance metrics for all endpoints.

    Returns:
        Dictionary with timing stats and slow endpoints.
    """
    profiler = get_profiler()
    return {
        "slow_endpoints": profiler.get_slow_endpoints(threshold_ms=100),
        "health_stats": profiler.get_stats("/api/health", "GET"),
    }


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    """WebSocket endpoint for chat with streaming LLM responses.

    Args:
        websocket: WebSocket connection from client.
    """
    await chat_websocket(websocket)


@app.websocket("/ws/research/{session_id}")
async def websocket_research_progress(websocket: WebSocket, session_id: str) -> None:
    """WebSocket endpoint for research progress updates.

    Args:
        websocket: WebSocket connection from client.
        session_id: Research session identifier.
    """
    await progress_handler.connect(session_id, websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
