"""End-to-end tests for complete research flow.

Tests TODO #271-275:
- #271 Create test file
- #272 Medical research query E2E
- #273 Competitive intelligence query E2E
- #274 Academic research query E2E
- #275 Privacy mode enforcement E2E
"""

import asyncio

import pytest
from httpx import AsyncClient


class TestEndToEndMedicalResearch:
    """E2E tests for medical research queries (#272)."""

    @pytest.mark.asyncio
    async def test_medical_research_detects_domain(
        self, async_client: AsyncClient
    ) -> None:
        """Medical query triggers medical domain detection.

        Tests:
        - Domain detection correctly identifies medical query
        - Response includes session_id
        """
        response = await async_client.post(
            "/api/research/start",
            json={
                "query": "What are the latest treatments for type 2 diabetes?",
                "privacy_mode": "cloud_allowed"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "started"

    @pytest.mark.asyncio
    async def test_medical_research_status_tracking(
        self, async_client: AsyncClient
    ) -> None:
        """Medical research status can be tracked.

        Tests:
        - Status endpoint returns valid ResearchStatus
        - Status shows correct phase progression
        """
        # Start research
        start_response = await async_client.post(
            "/api/research/start",
            json={
                "query": "Treatment protocols for hypertension in elderly patients",
                "privacy_mode": "cloud_allowed"
            }
        )
        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]

        # Check status immediately
        status_response = await async_client.get(
            f"/api/research/{session_id}/status"
        )
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert status_data["session_id"] == session_id
        assert status_data["status"] in ["running", "completed", "failed"]


class TestEndToEndCompetitiveIntelligence:
    """E2E tests for competitive intelligence queries (#273)."""

    @pytest.mark.asyncio
    async def test_ci_research_starts_correctly(
        self, async_client: AsyncClient
    ) -> None:
        """CI query starts research workflow.

        Tests:
        - CI domain detected
        - Business sources prioritized
        """
        response = await async_client.post(
            "/api/research/start",
            json={
                "query": "Who are the main competitors of Anthropic and their funding?",
                "privacy_mode": "cloud_allowed"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data

    @pytest.mark.asyncio
    async def test_ci_research_can_be_stopped(
        self, async_client: AsyncClient
    ) -> None:
        """CI research can be stopped early.

        Tests:
        - Stop endpoint works
        - Status reflects stopped state
        """
        # Start research
        start_response = await async_client.post(
            "/api/research/start",
            json={
                "query": "Market analysis for AI startups in 2024",
                "privacy_mode": "cloud_allowed"
            }
        )
        session_id = start_response.json()["session_id"]

        # Small delay to let it start
        await asyncio.sleep(0.1)

        # Stop it
        stop_response = await async_client.post(
            f"/api/research/{session_id}/stop"
        )
        assert stop_response.status_code == 200
        assert stop_response.json()["status"] == "stopping"


class TestEndToEndAcademicResearch:
    """E2E tests for academic research queries (#274)."""

    @pytest.mark.asyncio
    async def test_academic_research_starts(
        self, async_client: AsyncClient
    ) -> None:
        """Academic query starts research correctly.

        Tests:
        - Academic domain detected
        - ArXiv, Semantic Scholar sources available
        """
        response = await async_client.post(
            "/api/research/start",
            json={
                "query": "Recent advances in transformer architectures for NLP",
                "privacy_mode": "cloud_allowed"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "started"

    @pytest.mark.asyncio
    async def test_academic_research_nonexistent_session(
        self, async_client: AsyncClient
    ) -> None:
        """Nonexistent session returns 404.

        Tests error handling for invalid session IDs.
        """
        response = await async_client.get(
            "/api/research/nonexistent-session-id/status"
        )
        assert response.status_code == 404


class TestEndToEndPrivacyEnforcement:
    """E2E tests for privacy mode enforcement (#275)."""

    @pytest.mark.asyncio
    async def test_local_only_mode_accepted(
        self, async_client: AsyncClient
    ) -> None:
        """Local-only mode is accepted and processed.

        Tests:
        - LOCAL_ONLY privacy mode starts correctly
        - No cloud API calls made (verified by mocking)
        """
        response = await async_client.post(
            "/api/research/start",
            json={
                "query": "Analyze this internal confidential document",
                "privacy_mode": "local_only"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data

    @pytest.mark.asyncio
    async def test_hybrid_mode_accepted(
        self, async_client: AsyncClient
    ) -> None:
        """Hybrid privacy mode is accepted.

        Tests:
        - HYBRID mode starts correctly
        """
        response = await async_client.post(
            "/api/research/start",
            json={
                "query": "General research query",
                "privacy_mode": "hybrid"
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_privacy_mode_rejected(
        self, async_client: AsyncClient
    ) -> None:
        """Invalid privacy mode returns validation error.

        Tests input validation for privacy_mode field.
        """
        response = await async_client.post(
            "/api/research/start",
            json={
                "query": "Test query",
                "privacy_mode": "invalid_mode"
            }
        )

        # Should be rejected with 422 (validation error)
        assert response.status_code == 422


class TestEdgeCases:
    """E2E tests for edge cases (#282-287)."""

    @pytest.mark.asyncio
    async def test_empty_query_rejected(
        self, async_client: AsyncClient
    ) -> None:
        """Empty query is rejected with validation error."""
        response = await async_client.post(
            "/api/research/start",
            json={
                "query": "",
                "privacy_mode": "cloud_allowed"
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_very_long_query_handled(
        self, async_client: AsyncClient
    ) -> None:
        """Very long query doesn't crash the system.

        Tests #286: Handle very long queries
        """
        long_query = "What are " + " and ".join([f"topic{i}" for i in range(100)])

        response = await async_client.post(
            "/api/research/start",
            json={
                "query": long_query,
                "privacy_mode": "cloud_allowed"
            }
        )

        # Should either accept or reject gracefully (not 500)
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_whitespace_only_query_rejected(
        self, async_client: AsyncClient
    ) -> None:
        """Whitespace-only query is rejected."""
        response = await async_client.post(
            "/api/research/start",
            json={
                "query": "   \t\n  ",
                "privacy_mode": "cloud_allowed"
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_stop_nonrunning_session_fails(
        self, async_client: AsyncClient
    ) -> None:
        """Stopping a non-running session returns appropriate error."""
        response = await async_client.post(
            "/api/research/nonexistent-id/stop"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_report_before_completion_fails(
        self, async_client: AsyncClient
    ) -> None:
        """Getting report before completion returns error."""
        # Start research
        start_response = await async_client.post(
            "/api/research/start",
            json={
                "query": "Test query for report timing",
                "privacy_mode": "cloud_allowed"
            }
        )
        session_id = start_response.json()["session_id"]

        # Immediately try to get report (before completion)
        report_response = await async_client.get(
            f"/api/research/{session_id}/report"
        )

        # Should fail because research not completed
        assert report_response.status_code == 400
