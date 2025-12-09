"""Tests for process agent node."""

import pytest

from research_tool.agent.nodes.process import process_node


class TestProcessNode:
    """Test suite for process_node function."""

    @pytest.mark.asyncio
    async def test_process_returns_state_updates(self) -> None:
        """process_node returns dict with required keys."""
        state = {"original_query": "test query", "entities_found": []}
        result = await process_node(state)

        assert isinstance(result, dict)
        assert "facts_extracted" in result
        assert "current_phase" in result

    @pytest.mark.asyncio
    async def test_process_sets_current_phase(self) -> None:
        """process_node sets current_phase to 'process'."""
        state = {"original_query": "test query", "entities_found": []}
        result = await process_node(state)

        assert result["current_phase"] == "process"

    @pytest.mark.asyncio
    async def test_process_extracts_facts_from_entities(self) -> None:
        """process_node extracts facts from entities_found."""
        state = {
            "original_query": "test query",
            "entities_found": [
                {"title": "Entity 1", "url": "http://example.com/1"},
                {"title": "Entity 2", "url": "http://example.com/2"},
            ]
        }
        result = await process_node(state)

        assert len(result["facts_extracted"]) == 2
        assert "Entity 1" in result["facts_extracted"][0]["statement"]
        assert result["facts_extracted"][0]["source"] == "http://example.com/1"

    @pytest.mark.asyncio
    async def test_process_handles_empty_entities(self) -> None:
        """process_node handles empty entities_found gracefully."""
        state = {"original_query": "test query", "entities_found": []}
        result = await process_node(state)

        assert result["facts_extracted"] == []

    @pytest.mark.asyncio
    async def test_process_handles_missing_entities_key(self) -> None:
        """process_node handles missing entities_found key."""
        state = {"original_query": "test query"}
        result = await process_node(state)

        assert result["facts_extracted"] == []

    @pytest.mark.asyncio
    async def test_process_limits_facts_to_10(self) -> None:
        """process_node limits facts to first 10 entities."""
        entities = [
            {"title": f"Entity {i}", "url": f"http://example.com/{i}"}
            for i in range(20)
        ]
        state = {"original_query": "test", "entities_found": entities}
        result = await process_node(state)

        assert len(result["facts_extracted"]) == 10

    @pytest.mark.asyncio
    async def test_process_facts_have_required_fields(self) -> None:
        """Extracted facts have statement, source, and confidence."""
        state = {
            "original_query": "test",
            "entities_found": [{"title": "Test", "url": "http://test.com"}]
        }
        result = await process_node(state)

        fact = result["facts_extracted"][0]
        assert "statement" in fact
        assert "source" in fact
        assert "confidence" in fact

    @pytest.mark.asyncio
    async def test_process_facts_have_confidence_score(self) -> None:
        """Extracted facts include confidence score."""
        state = {
            "original_query": "test",
            "entities_found": [{"title": "Test", "url": "http://test.com"}]
        }
        result = await process_node(state)

        assert result["facts_extracted"][0]["confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_process_handles_entity_without_title(self) -> None:
        """process_node handles entity missing title."""
        state = {
            "original_query": "test",
            "entities_found": [{"url": "http://test.com"}]  # No title
        }
        result = await process_node(state)

        assert "Unknown" in result["facts_extracted"][0]["statement"]
