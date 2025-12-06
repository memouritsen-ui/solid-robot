"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from research_tool.core import Settings, get_logger

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


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Dictionary with status and version.
    """
    return {"status": "healthy", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
