"""Pytest fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from research_tool.main import app


@pytest.fixture
def client() -> TestClient:
    """Synchronous test client.

    Returns:
        TestClient configured for the FastAPI app.
    """
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncClient:  # type: ignore[misc]
    """Asynchronous test client.

    Yields:
        AsyncClient configured for the FastAPI app.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://test",
    ) as ac:
        yield ac
