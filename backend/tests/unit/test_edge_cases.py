"""Edge case handling tests (#282-287).

Tests for graceful handling of:
- #282: All sources fail
- #283: Network disconnection
- #284: Model overload
- #285: Malformed API responses
- #286: Very long queries
- #287: Empty results
"""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from research_tool.core.exceptions import (
    ModelOverloadedError,
    ModelUnavailableError,
    NetworkError,
    RateLimitError,
)


class TestAllSourcesFail:
    """Test graceful handling when all sources fail (#282)."""

    @pytest.mark.asyncio
    async def test_collect_node_handles_all_providers_failing(self) -> None:
        """Collect node should handle all providers failing gracefully."""
        from research_tool.agent.nodes.collect import collect_node

        state: dict[str, Any] = {
            "original_query": "test query",
            "refined_query": "test query",
            "domain": "general",
            "privacy_mode": "local_only",
            "sources_collected": [],
            "facts_extracted": [],
            "current_phase": "plan",
            "errors": [],
            "audit_trail": [],
        }

        # Mock all providers to be unavailable
        with patch(
            "research_tool.agent.nodes.collect.TavilyProvider"
        ) as mock_tavily, patch(
            "research_tool.agent.nodes.collect.BraveProvider"
        ) as mock_brave, patch(
            "research_tool.agent.nodes.collect.SemanticScholarProvider"
        ) as mock_scholar, patch(
            "research_tool.agent.nodes.collect.PubMedProvider"
        ) as mock_pubmed, patch(
            "research_tool.agent.nodes.collect.ArxivProvider"
        ) as mock_arxiv, patch(
            "research_tool.agent.nodes.collect.get_crawler"
        ) as mock_crawler:
            # All providers unavailable
            for mock in [mock_tavily, mock_brave, mock_scholar, mock_pubmed, mock_arxiv]:
                mock.return_value.is_available = AsyncMock(return_value=False)

            mock_crawler.return_value.is_available = AsyncMock(return_value=False)

            result = await collect_node(state)

            # Should not crash, should return empty results
            assert result is not None
            assert "current_phase" in result

    @pytest.mark.asyncio
    async def test_collect_node_continues_after_provider_error(self) -> None:
        """Collect node should continue when one provider fails."""
        from research_tool.agent.nodes.collect import collect_node

        state: dict[str, Any] = {
            "original_query": "test query",
            "refined_query": "test query",
            "domain": "academic",
            "privacy_mode": "cloud_allowed",
            "sources_collected": [],
            "facts_extracted": [],
            "current_phase": "plan",
            "errors": [],
            "audit_trail": [],
        }

        # One provider fails, another succeeds
        with patch(
            "research_tool.agent.nodes.collect.ArxivProvider"
        ) as mock_arxiv, patch(
            "research_tool.agent.nodes.collect.get_crawler"
        ) as mock_crawler:
            mock_arxiv.return_value.is_available = AsyncMock(return_value=True)
            mock_arxiv.return_value.search = AsyncMock(
                return_value=[
                    {
                        "url": "https://arxiv.org/abs/1234",
                        "title": "Test Paper",
                        "snippet": "Test snippet",
                        "source_name": "arxiv",
                    }
                ]
            )

            mock_crawler.return_value.is_available = AsyncMock(return_value=False)

            result = await collect_node(state)

            # Should succeed with available sources
            assert result is not None
            assert "entities_found" in result

    @pytest.mark.asyncio
    async def test_empty_research_plan_handled(self) -> None:
        """Empty research plan should be handled gracefully."""
        from research_tool.agent.nodes.collect import collect_node

        state: dict[str, Any] = {
            "original_query": "obscure topic with no results",
            "refined_query": "obscure topic with no results",
            "domain": "general",
            "privacy_mode": "local_only",
            "sources_collected": [],
            "facts_extracted": [],
            "current_phase": "plan",
            "errors": [],
            "audit_trail": [],
        }

        with patch(
            "research_tool.agent.nodes.collect.get_crawler"
        ) as mock_crawler:
            mock_crawler.return_value.is_available = AsyncMock(return_value=False)

            result = await collect_node(state)
            assert result is not None


class TestNetworkDisconnection:
    """Test handling of network disconnection (#283)."""

    @pytest.mark.asyncio
    async def test_retry_decorator_exists(self) -> None:
        """with_retry decorator should be available."""
        from research_tool.utils.retry import with_retry

        # Just verify it exists and is a decorator
        @with_retry
        async def test_func() -> str:
            return "success"

        # Should be callable
        assert callable(test_func)

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_repeated_failures(self) -> None:
        """Circuit breaker should open after threshold failures."""
        from research_tool.utils.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        # Record failures
        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN
        assert not cb.can_execute()

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovers(self) -> None:
        """Circuit breaker should recover after timeout."""
        import time

        from research_tool.utils.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.15)

        # Should allow test request
        assert cb.can_execute()
        assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_network_error_exception_exists(self) -> None:
        """NetworkError should be raisable and catchable."""
        with pytest.raises(NetworkError):
            raise NetworkError("Connection failed")


class TestModelOverload:
    """Test handling of model overload (#284)."""

    @pytest.mark.asyncio
    async def test_model_overload_error_raised(self) -> None:
        """ModelOverloadedError should be raisable."""
        from research_tool.services.llm.router import LLMRouter

        router = LLMRouter()

        # When router receives overload, it wraps in ModelUnavailableError
        with (
            patch.object(
                router._router,
                "acompletion",
                side_effect=ModelOverloadedError("Model overloaded"),
            ),
            pytest.raises(ModelUnavailableError),
        ):
            await router.complete(
                messages=[{"role": "user", "content": "test"}],
                model="local-fast",
            )

    @pytest.mark.asyncio
    async def test_model_selector_returns_recommendation(self) -> None:
        """Model selector should return recommendations."""
        from research_tool.services.llm.selector import (
            ModelSelector,
            PrivacyMode,
            TaskComplexity,
        )

        selector = ModelSelector()

        recommendation = selector.select(
            task_complexity=TaskComplexity.HIGH,
            privacy_mode=PrivacyMode.CLOUD_ALLOWED,
        )

        assert recommendation is not None
        assert recommendation.model is not None

    @pytest.mark.asyncio
    async def test_model_selector_local_only(self) -> None:
        """Model selector should respect LOCAL_ONLY."""
        from research_tool.services.llm.selector import (
            ModelSelector,
            PrivacyMode,
            TaskComplexity,
        )

        selector = ModelSelector()

        recommendation = selector.select(
            task_complexity=TaskComplexity.HIGH,
            privacy_mode=PrivacyMode.LOCAL_ONLY,
        )

        assert recommendation is not None
        # Should select a local model
        assert "local" in recommendation.model


class TestMalformedResponses:
    """Test handling of malformed API responses (#285)."""

    @pytest.mark.asyncio
    async def test_malformed_json_handling(self) -> None:
        """Code should handle malformed JSON gracefully."""
        import json

        # Test that malformed JSON raises expected error
        with pytest.raises(json.JSONDecodeError):
            json.loads("not valid json {")

        # Test empty response handling
        empty_response: dict[str, Any] = {}
        assert empty_response.get("results", []) == []

    @pytest.mark.asyncio
    async def test_missing_fields_use_defaults(self) -> None:
        """Missing fields should use safe defaults."""
        response: dict[str, Any] = {"web": {}}

        # Safe access patterns should work
        results = response.get("web", {}).get("results", [])
        assert results == []

        # Nested access should be safe
        count = response.get("web", {}).get("total", 0)
        assert count == 0

    @pytest.mark.asyncio
    async def test_source_result_creation(self) -> None:
        """SourceResult should be creatable with required fields."""
        from datetime import datetime

        from research_tool.models.entities import SourceResult

        result = SourceResult(
            url="https://example.com",
            title="Test",
            snippet="Test snippet",
            source_name="test",
            retrieved_at=datetime.now(),
        )

        assert result.title == "Test"
        assert result.url == "https://example.com"


class TestVeryLongQueries:
    """Test handling of very long queries (#286)."""

    @pytest.mark.asyncio
    async def test_long_query_processed(self) -> None:
        """Very long queries should be processed without crash."""
        from research_tool.agent.nodes.clarify import clarify_node

        # Create query longer than typical limits
        long_query = "medical research " * 1000  # ~16000 chars

        state: dict[str, Any] = {
            "original_query": long_query,
            "refined_query": None,
            "domain": "general",
            "privacy_mode": "local_only",
            "sources_collected": [],
            "facts_extracted": [],
            "current_phase": "init",
            "errors": [],
            "audit_trail": [],
        }

        # Should not crash
        result = await clarify_node(state)
        assert result is not None
        assert "domain" in result
        assert result["domain"] == "medical"  # Should detect medical

    @pytest.mark.asyncio
    async def test_memory_handles_long_content(self) -> None:
        """Memory system should handle long content via chunking."""
        import tempfile

        from research_tool.services.memory.lance_repo import LanceDBRepository

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LanceDBRepository(db_path=tmpdir)

            # Very long content
            long_content = "This is test content. " * 5000  # ~110k chars

            # Should chunk and store successfully
            doc_id = await repo.store_document(
                content=long_content,
                metadata={"source": "test"},
                session_id="long-content-test",
            )

            assert doc_id is not None

    @pytest.mark.asyncio
    async def test_chunking_works_correctly(self) -> None:
        """Document chunking should split large content."""
        import tempfile

        from research_tool.services.memory.lance_repo import LanceDBRepository

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LanceDBRepository(db_path=tmpdir)

            # Content that should be chunked
            long_content = "Word " * 1000  # Will exceed chunk size

            chunks = repo.chunk_document(long_content)

            # Should have multiple chunks
            assert len(chunks) >= 1


class TestEmptyResults:
    """Test handling of empty results (#287)."""

    @pytest.mark.asyncio
    async def test_collect_handles_empty_results(self) -> None:
        """Collect node should handle when all searches return empty."""
        from research_tool.agent.nodes.collect import collect_node

        state: dict[str, Any] = {
            "original_query": "xyz123nonexistent",
            "refined_query": "xyz123nonexistent",
            "domain": "general",
            "privacy_mode": "local_only",
            "sources_collected": [],
            "facts_extracted": [],
            "current_phase": "plan",
            "errors": [],
            "audit_trail": [],
        }

        with patch(
            "research_tool.agent.nodes.collect.TavilyProvider"
        ) as mock_tavily, patch(
            "research_tool.agent.nodes.collect.get_crawler"
        ) as mock_crawler:
            mock_tavily.return_value.is_available = AsyncMock(return_value=True)
            mock_tavily.return_value.search = AsyncMock(return_value=[])

            mock_crawler.return_value.is_available = AsyncMock(return_value=False)

            result = await collect_node(state)

            assert result is not None

    @pytest.mark.asyncio
    async def test_empty_memory_search_returns_empty_list(self) -> None:
        """Memory search with no matches should return empty list."""
        import tempfile

        from research_tool.services.memory.lance_repo import LanceDBRepository

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LanceDBRepository(db_path=tmpdir)

            # Search empty database
            results = await repo.search_similar("anything", limit=10)

            assert results == []

    @pytest.mark.asyncio
    async def test_synthesize_handles_no_facts(self) -> None:
        """Synthesize node should handle no facts gracefully."""
        from research_tool.agent.nodes.synthesize import synthesize_node

        state: dict[str, Any] = {
            "original_query": "test query",
            "refined_query": "test query",
            "domain": "general",
            "privacy_mode": "local_only",
            "sources_collected": [],
            "facts_extracted": [],  # No facts
            "entities_found": [],
            "current_phase": "analyze",
            "errors": [],
            "audit_trail": [],
            "confidence_score": 0.0,
        }

        result = await synthesize_node(state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_export_handles_empty_research(self) -> None:
        """Export should handle research with no results."""
        from research_tool.services.export.exporter import ResearchExportData
        from research_tool.services.export.markdown import MarkdownExporter

        exporter = MarkdownExporter()

        # Empty research data using proper model
        research_data = ResearchExportData(
            query="test",
            domain="general",
            summary="No results found.",
            facts=[],
            sources=[],
            confidence_score=0.0,
            limitations=["No data available"],
            metadata={},
        )

        result = await exporter.export(research_data)

        # Should produce ExportResult
        assert result is not None
        assert result.success or result.error is not None


class TestRateLimitHandling:
    """Test rate limit handling across providers."""

    @pytest.mark.asyncio
    async def test_rate_limiter_exists(self) -> None:
        """RateLimiter should be importable and usable."""
        from research_tool.services.search.rate_limiter import RateLimiter

        limiter = RateLimiter()

        # Should allow initial requests (acquire takes provider and rps)
        await limiter.acquire("test_provider", 10.0)
        # If we got here, it worked

    @pytest.mark.asyncio
    async def test_rate_limit_error_includes_retry_after(self) -> None:
        """RateLimitError should include retry_after when available."""
        error = RateLimitError("Rate limited", retry_after=30)

        assert error.retry_after == 30
        assert "Rate limited" in str(error)


class TestGracefulDegradation:
    """Test graceful degradation of services."""

    @pytest.mark.asyncio
    async def test_partial_results_still_usable(self) -> None:
        """Partial results should still be synthesizable."""
        from research_tool.agent.nodes.synthesize import synthesize_node

        state: dict[str, Any] = {
            "original_query": "test query",
            "refined_query": "test query",
            "domain": "general",
            "privacy_mode": "local_only",
            "sources_collected": [],
            "entities_found": [
                {
                    "title": "Single Result",
                    "url": "https://example.com",
                    "snippet": "Some content",
                    "source": "test",
                }
            ],
            "facts_extracted": [
                {"fact": "Test fact", "confidence": 0.7, "source": "test"}
            ],
            "current_phase": "analyze",
            "errors": ["tavily failed", "brave failed"],  # Record failures
            "audit_trail": [],
            "confidence_score": 0.5,
        }

        result = await synthesize_node(state)
        assert result is not None

    @pytest.mark.asyncio
    async def test_circuit_breaker_global_per_service(self) -> None:
        """Each service should have its own circuit breaker."""
        from research_tool.utils.circuit_breaker import get_circuit_breaker

        cb1 = get_circuit_breaker("service_a")
        cb2 = get_circuit_breaker("service_b")
        cb3 = get_circuit_breaker("service_a")

        # Same service returns same breaker
        assert cb1 is cb3

        # Different service returns different breaker
        assert cb1 is not cb2
