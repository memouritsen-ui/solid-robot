"""End-to-end tests for complete research workflow."""

import pytest


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_basic_health(self, async_client):
        """Basic health check should return healthy."""
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_detailed_health(self, async_client):
        """Detailed health should return component status."""
        response = await async_client.get("/api/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "components" in data
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_config_status(self, async_client):
        """Config endpoint should return safe config."""
        response = await async_client.get("/api/health/config")
        assert response.status_code == 200
        data = response.json()
        assert "features" in data
        # Should not expose actual keys
        if data["config"].get("anthropic_api_key"):
            assert data["config"]["anthropic_api_key"] == "***"


class TestResearchWorkflow:
    """Test research workflow endpoints."""

    @pytest.mark.asyncio
    async def test_start_research(self, async_client):
        """Should start research session."""
        response = await async_client.post(
            "/api/research/start",
            json={
                "query": "What is machine learning?",
                "privacy_mode": "cloud_allowed"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "started"

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, async_client):
        """Should return 404 for unknown session."""
        response = await async_client.get("/api/research/nonexistent-id/status")
        assert response.status_code == 404


class TestExportEndpoints:
    """Test export functionality."""

    @pytest.mark.asyncio
    async def test_export_formats(self, async_client):
        """Should list available export formats."""
        response = await async_client.get("/api/export/formats")
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert "markdown" in data["formats"]
        assert "pdf" in data["formats"]
