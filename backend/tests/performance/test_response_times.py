"""Performance tests for response time requirements.

Requirements from TODO.md #276-281:
- #278: <2s first token (local LLM)
- #279: <1s first token (cloud LLM)
- #280: <100ms memory retrieval
- #281: <5min typical research

These tests verify performance baselines and track regressions.
"""

import asyncio
import time
from typing import Any
from unittest.mock import patch

import pytest


class TestHealthEndpointPerformance:
    """Test health endpoint response time."""

    @pytest.mark.asyncio
    async def test_health_endpoint_under_50ms(self) -> None:
        """Health endpoint should respond in under 50ms."""
        from fastapi.testclient import TestClient

        from research_tool.main import app

        client = TestClient(app)

        # Warm up
        client.get("/api/health")

        # Measure
        times: list[float] = []
        for _ in range(10):
            start = time.perf_counter()
            response = client.get("/api/health")
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            assert response.status_code == 200

        avg_time = sum(times) / len(times)
        assert avg_time < 0.05, f"Health endpoint took {avg_time*1000:.1f}ms avg (>50ms)"


class TestMemoryRetrievalPerformance:
    """Test memory system performance requirements (#280)."""

    @pytest.mark.asyncio
    async def test_memory_search_under_100ms(self) -> None:
        """Memory retrieval should complete in under 100ms (#280)."""
        import tempfile

        from research_tool.services.memory.lance_repo import LanceDBRepository

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LanceDBRepository(db_path=tmpdir)

            # Insert test data using correct API signature
            for i in range(100):
                await repo.store_document(
                    content=f"Test document {i} with some content about machine learning and AI.",
                    metadata={
                        "source_url": f"https://example.com/doc{i}",
                        "source_type": "test",
                        "index": i,
                    },
                    session_id="perf-test-session",
                )

            # Measure search time
            times: list[float] = []
            for _ in range(10):
                start = time.perf_counter()
                await repo.search_similar("machine learning", limit=10)
                elapsed = time.perf_counter() - start
                times.append(elapsed)

            avg_time = sum(times) / len(times)
            assert (
                avg_time < 0.1
            ), f"Memory search took {avg_time*1000:.1f}ms avg (>100ms)"

    @pytest.mark.asyncio
    async def test_memory_retrieval_scales_with_data(self) -> None:
        """Memory retrieval should stay under 100ms with larger datasets."""
        import tempfile

        from research_tool.services.memory.lance_repo import LanceDBRepository

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LanceDBRepository(db_path=tmpdir)

            # Insert larger dataset using correct API
            for i in range(500):
                await repo.store_document(
                    content=f"Document {i}: Research on topic {i % 50} with detailed analysis.",
                    metadata={
                        "source_url": f"https://source{i}.com",
                        "source_type": "academic",
                        "batch": i // 100,
                    },
                    session_id="scale-test-session",
                )

            # Measure
            start = time.perf_counter()
            await repo.search_similar("research analysis", limit=20)
            elapsed = time.perf_counter() - start

            assert elapsed < 0.1, f"Search with 500 docs took {elapsed*1000:.1f}ms (>100ms)"


class TestLLMFirstTokenLatency:
    """Test LLM first token latency requirements (#278, #279)."""

    @pytest.mark.asyncio
    async def test_local_llm_first_token_under_2s(self) -> None:
        """Local LLM should return first token in under 2s (#278).

        This test mocks the LLM to verify the infrastructure overhead
        is minimal. Real latency depends on Ollama model.
        """
        from research_tool.services.llm.router import LLMRouter

        router = LLMRouter()

        # Mock streaming completion
        async def mock_stream(*args: Any, **kwargs: Any) -> Any:
            """Simulate streaming with 100ms first token."""
            yield "First"
            await asyncio.sleep(0.05)
            yield " token"

        with patch.object(router, "_stream_completion", side_effect=mock_stream):
            start = time.perf_counter()
            first_token_time = None

            # Use complete with stream=True
            result = await router.complete(
                messages=[{"role": "user", "content": "test"}],
                model="local-fast",
                stream=True,
            )

            async for _token in result:
                if first_token_time is None:
                    first_token_time = time.perf_counter() - start
                    break

            assert (
                first_token_time is not None and first_token_time < 2.0
            ), f"First token took {first_token_time:.2f}s (>2s)"

    @pytest.mark.asyncio
    async def test_cloud_llm_first_token_under_1s(self) -> None:
        """Cloud LLM should return first token in under 1s (#279).

        This test mocks the LLM to verify infrastructure overhead.
        Real latency depends on network and API.
        """
        from research_tool.services.llm.router import LLMRouter

        router = LLMRouter()

        # Mock streaming completion
        async def mock_stream(*args: Any, **kwargs: Any) -> Any:
            """Simulate streaming with 50ms first token."""
            yield "Hello"
            await asyncio.sleep(0.02)
            yield " there"

        with patch.object(router, "_stream_completion", side_effect=mock_stream):
            start = time.perf_counter()
            first_token_time = None

            result = await router.complete(
                messages=[{"role": "user", "content": "test"}],
                model="cloud-best",
                stream=True,
            )

            async for _token in result:
                if first_token_time is None:
                    first_token_time = time.perf_counter() - start
                    break

            assert (
                first_token_time is not None and first_token_time < 1.0
            ), f"First token took {first_token_time:.2f}s (>1s)"


class TestResearchWorkflowPerformance:
    """Test research workflow timing (#281)."""

    @pytest.mark.asyncio
    async def test_simple_research_workflow_timing(self) -> None:
        """A simple research workflow should complete phases quickly.

        This tests the agent node execution overhead, not actual
        LLM calls or network requests.
        """
        from research_tool.agent.nodes.clarify import clarify_node

        # Create minimal state as dict (ResearchState is a TypedDict)
        state: dict[str, Any] = {
            "original_query": "test query about medical research",
            "refined_query": None,
            "domain": "general",
            "privacy_mode": "local_only",
            "sources_collected": [],
            "facts_extracted": [],
            "synthesis": "",
            "confidence_score": 0.0,
            "iteration_count": 0,
            "current_phase": "init",
            "errors": [],
            "audit_trail": [],
        }

        start = time.perf_counter()
        result = await clarify_node(state)
        elapsed = time.perf_counter() - start

        # Node overhead should be <100ms
        # This tests initialization and state management overhead
        assert elapsed < 0.1, f"Clarify node overhead was {elapsed*1000:.1f}ms (>100ms)"
        assert result["domain"] == "medical"  # Should detect medical domain

    @pytest.mark.asyncio
    async def test_agent_graph_initialization_fast(self) -> None:
        """Agent graph should initialize quickly."""
        start = time.perf_counter()

        from research_tool.agent.graph import create_research_graph

        graph = create_research_graph()
        elapsed = time.perf_counter() - start

        assert graph is not None
        assert elapsed < 0.5, f"Graph init took {elapsed*1000:.1f}ms (>500ms)"


class TestAPIEndpointPerformance:
    """Test API endpoint response times."""

    def test_export_formats_endpoint_fast(self) -> None:
        """GET /api/export/formats should respond quickly."""
        from fastapi.testclient import TestClient

        from research_tool.main import app

        client = TestClient(app)

        # Warm up
        client.get("/api/export/formats")

        # Measure
        times: list[float] = []
        for _ in range(5):
            start = time.perf_counter()
            response = client.get("/api/export/formats")
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            assert response.status_code == 200

        avg_time = sum(times) / len(times)
        assert avg_time < 0.05, f"Export formats took {avg_time*1000:.1f}ms avg (>50ms)"


class TestProfileMetrics:
    """Tests for profiling metrics collection."""

    @pytest.mark.asyncio
    async def test_timing_middleware_captures_request_time(self) -> None:
        """Timing middleware should capture request duration."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from research_tool.utils.profiling import TimingMiddleware

        app = FastAPI()
        captured_times: list[float] = []

        def on_timing(path: str, method: str, duration: float) -> None:
            captured_times.append(duration)

        app.add_middleware(TimingMiddleware, callback=on_timing)

        @app.get("/test")
        async def test_endpoint() -> dict[str, str]:
            await asyncio.sleep(0.01)  # 10ms
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert len(captured_times) == 1
        assert captured_times[0] >= 0.01  # At least 10ms

    @pytest.mark.asyncio
    async def test_timing_middleware_handles_errors(self) -> None:
        """Timing middleware should still capture time on errors."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from research_tool.utils.profiling import TimingMiddleware

        app = FastAPI()
        captured_times: list[float] = []

        def on_timing(path: str, method: str, duration: float) -> None:
            captured_times.append(duration)

        app.add_middleware(TimingMiddleware, callback=on_timing)

        @app.get("/error")
        async def error_endpoint() -> None:
            raise ValueError("Test error")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        assert response.status_code == 500
        assert len(captured_times) == 1  # Still captured
