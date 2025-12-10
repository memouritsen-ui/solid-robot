"""Tests for export agent node including source effectiveness updates.

TDD: Tests first, no mocks for core behavior.
#226: Update source effectiveness after research
"""

import pytest

from research_tool.agent.nodes.export_node import export_node


class TestExportNode:
    """Test suite for export_node function."""

    @pytest.mark.asyncio
    async def test_export_returns_state_updates(self) -> None:
        """export_node returns dict with required keys."""
        state = {
            "session_id": "test-123",
            "original_query": "test query",
            "domain": "general",
            "final_report": {"summary": "test report"},
        }
        result = await export_node(state)

        assert isinstance(result, dict)
        assert "current_phase" in result

    @pytest.mark.asyncio
    async def test_export_sets_current_phase(self) -> None:
        """export_node sets current_phase to 'export'."""
        state = {
            "session_id": "test-123",
            "final_report": {"summary": "test"},
        }
        result = await export_node(state)

        assert result["current_phase"] == "export"

    @pytest.mark.asyncio
    async def test_export_handles_missing_report(self) -> None:
        """export_node handles missing final_report gracefully."""
        state = {"session_id": "test-123"}
        result = await export_node(state)

        assert result["export_ready"] is False
        assert "export_error" in result

    @pytest.mark.asyncio
    async def test_export_marks_ready_with_report(self) -> None:
        """export_node marks export ready when report exists."""
        state = {
            "session_id": "test-123",
            "final_report": {"summary": "test report"},
        }
        result = await export_node(state)

        assert result["export_ready"] is True


class TestExportNodeSourceEffectivenessUpdate:
    """Tests for source effectiveness updates in export_node.

    #226: Update source effectiveness after research
    Tests verify learning is triggered and returns correct summary.
    """

    @pytest.mark.asyncio
    async def test_export_triggers_learning_for_sources(self) -> None:
        """export_node triggers learning and updates sources."""
        state = {
            "session_id": "test-123",
            "domain": "medical",
            "sources_queried": ["pubmed", "semantic_scholar"],
            "facts_extracted": [
                {"source": "pubmed", "confidence": 0.9, "statement": "fact 1"},
                {"source": "pubmed", "confidence": 0.8, "statement": "fact 2"},
                {"source": "semantic_scholar", "confidence": 0.7, "statement": "fact 3"},
            ],
            "access_failures": [],
            "final_report": {"summary": "test report"},
        }

        result = await export_node(state)

        # Learning should have been triggered for both sources
        assert result["learning_summary"]["sources_updated"] == 2

    @pytest.mark.asyncio
    async def test_export_includes_failed_sources_in_learning(self) -> None:
        """export_node includes sources with access failures in learning."""
        state = {
            "session_id": "test-456",
            "domain": "medical",
            "sources_queried": ["pubmed", "failing_source"],
            "facts_extracted": [
                {"source": "pubmed", "confidence": 0.9, "statement": "fact 1"},
            ],
            "access_failures": [
                {"source": "failing_source", "error": "rate_limited"},
            ],
            "final_report": {"summary": "test report"},
        }

        result = await export_node(state)

        # Both sources should be updated (pubmed success, failing_source failure)
        assert result["learning_summary"]["sources_updated"] == 2

    @pytest.mark.asyncio
    async def test_export_returns_learning_summary(self) -> None:
        """export_node returns learning summary in result."""
        state = {
            "session_id": "test-789",
            "domain": "academic",
            "sources_queried": ["arxiv"],
            "facts_extracted": [{"source": "arxiv", "confidence": 0.8}],
            "access_failures": [],
            "final_report": {"summary": "test"},
        }

        result = await export_node(state)

        # Should include learning summary
        assert "learning_summary" in result
        assert "sources_updated" in result["learning_summary"]

    @pytest.mark.asyncio
    async def test_export_handles_empty_sources(self) -> None:
        """export_node handles empty sources_queried gracefully."""
        state = {
            "session_id": "test-empty",
            "domain": "general",
            "sources_queried": [],
            "facts_extracted": [],
            "access_failures": [],
            "final_report": {"summary": "empty research"},
        }

        result = await export_node(state)

        # Should still work, with 0 sources updated
        assert result["export_ready"] is True
        assert result.get("learning_summary", {}).get("sources_updated", 0) == 0

    @pytest.mark.asyncio
    async def test_export_handles_missing_domain(self) -> None:
        """export_node uses 'general' domain when domain is missing."""
        state = {
            "session_id": "test-no-domain",
            "sources_queried": ["brave"],
            "facts_extracted": [{"source": "brave", "confidence": 0.7}],
            "access_failures": [],
            "final_report": {"summary": "test"},
        }

        # Should not raise
        result = await export_node(state)
        assert result["current_phase"] == "export"


class TestExportNodeDomainConfigUpdate:
    """Tests for domain config updates in export_node.

    #227: Update domain config based on discovered sources
    """

    @pytest.mark.asyncio
    async def test_export_updates_preferred_sources(self) -> None:
        """export_node updates preferred_sources based on high-performing sources."""
        state = {
            "session_id": "test-227-a",
            "domain": "medical",
            "sources_queried": ["pubmed", "semantic_scholar", "arxiv"],
            "facts_extracted": [
                # pubmed performed best
                {"source": "pubmed", "confidence": 0.95, "statement": "fact 1"},
                {"source": "pubmed", "confidence": 0.90, "statement": "fact 2"},
                {"source": "pubmed", "confidence": 0.85, "statement": "fact 3"},
                # semantic_scholar also good
                {"source": "semantic_scholar", "confidence": 0.80, "statement": "fact 4"},
                # arxiv lower performance
                {"source": "arxiv", "confidence": 0.50, "statement": "fact 5"},
            ],
            "access_failures": [],
            "final_report": {"summary": "test"},
        }

        result = await export_node(state)

        # Should include domain_config_updated in learning_summary
        assert "domain_config_updated" in result["learning_summary"]

    @pytest.mark.asyncio
    async def test_export_updates_excluded_sources(self) -> None:
        """export_node adds consistently failing sources to excluded_sources."""
        state = {
            "session_id": "test-227-b",
            "domain": "academic",
            "sources_queried": ["arxiv", "bad_source"],
            "facts_extracted": [
                {"source": "arxiv", "confidence": 0.85, "statement": "fact 1"},
            ],
            "access_failures": [
                {"source": "bad_source", "error": "permanent_failure"},
            ],
            "final_report": {"summary": "test"},
        }

        result = await export_node(state)

        # Learning summary should indicate config was updated
        assert result["learning_summary"].get("domain_config_updated", False)

    @pytest.mark.asyncio
    async def test_export_discovers_new_effective_sources(self) -> None:
        """export_node identifies newly discovered effective sources."""
        state = {
            "session_id": "test-227-c",
            "domain": "regulatory",
            "sources_queried": ["tavily", "new_great_source"],
            "facts_extracted": [
                {"source": "tavily", "confidence": 0.70, "statement": "fact 1"},
                # new_great_source performed excellently
                {"source": "new_great_source", "confidence": 0.95, "statement": "fact 2"},
                {"source": "new_great_source", "confidence": 0.92, "statement": "fact 3"},
            ],
            "access_failures": [],
            "final_report": {"summary": "test"},
        }

        result = await export_node(state)

        # Should report discovered sources
        learning = result["learning_summary"]
        assert learning.get("sources_updated", 0) >= 2
