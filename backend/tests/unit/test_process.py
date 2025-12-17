"""Tests for process agent node."""

from unittest.mock import AsyncMock, patch

import pytest

from research_tool.agent.nodes.process import (
    deduplicate_facts,
    extract_facts_with_llm,
    process_node,
)


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
        """process_node extracts facts from entities with content."""
        # Mock LLM response
        mock_llm_response = '[{"statement": "Fact from Entity 1", "confidence": 0.8}]'

        with patch(
            "research_tool.agent.nodes.process.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value=mock_llm_response)
            mock_get_router.return_value = mock_router

            state = {
                "original_query": "test query",
                "entities_found": [
                    {
                        "title": "Entity 1",
                        "url": "http://example.com/1",
                        "full_content": "This is the full content of entity 1 with facts."
                    },
                    {
                        "title": "Entity 2",
                        "url": "http://example.com/2",
                        "snippet": "This is a snippet from entity 2."
                    },
                ]
            }
            result = await process_node(state)

            assert len(result["facts_extracted"]) >= 1
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
    async def test_process_skips_entities_without_content(self) -> None:
        """process_node skips entities that have no content."""
        state = {
            "original_query": "test",
            "entities_found": [
                {"title": "No Content", "url": "http://example.com/1"},
                {"title": "Empty Content", "url": "http://example.com/2", "full_content": ""},
            ]
        }
        result = await process_node(state)

        # Should skip entities without content
        assert result["facts_extracted"] == []

    @pytest.mark.asyncio
    async def test_process_uses_snippet_when_no_full_content(self) -> None:
        """process_node falls back to snippet when full_content is missing."""
        mock_llm_response = '[{"statement": "Fact from snippet", "confidence": 0.7}]'

        with patch(
            "research_tool.agent.nodes.process.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value=mock_llm_response)
            mock_get_router.return_value = mock_router

            state = {
                "original_query": "test",
                "entities_found": [
                    {
                        "title": "Snippet Only",
                        "url": "http://example.com/1",
                        "snippet": "This is a snippet with factual information."
                    }
                ]
            }
            result = await process_node(state)

            assert len(result["facts_extracted"]) == 1


class TestExtractFactsWithLLM:
    """Test suite for extract_facts_with_llm function."""

    @pytest.mark.asyncio
    async def test_extract_returns_empty_for_empty_content(self) -> None:
        """extract_facts_with_llm returns empty list for empty content."""
        result = await extract_facts_with_llm("", "http://test.com", "test query")
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_returns_empty_for_whitespace_content(self) -> None:
        """extract_facts_with_llm returns empty for whitespace-only content."""
        result = await extract_facts_with_llm("   \n\t  ", "http://test.com", "test")
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_parses_llm_json_response(self) -> None:
        """extract_facts_with_llm correctly parses LLM JSON response."""
        mock_response = '[{"statement": "Test fact", "confidence": 0.9}]'

        with patch(
            "research_tool.agent.nodes.process.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value=mock_response)
            mock_get_router.return_value = mock_router

            result = await extract_facts_with_llm(
                "Some content with facts",
                "http://test.com",
                "test query"
            )

            assert len(result) == 1
            assert result[0]["statement"] == "Test fact"
            assert result[0]["confidence"] == 0.9
            assert result[0]["source"] == "http://test.com"
            assert result[0]["extracted_by"] == "llm"

    @pytest.mark.asyncio
    async def test_extract_handles_markdown_code_blocks(self) -> None:
        """extract_facts_with_llm handles markdown-wrapped JSON."""
        mock_response = '```json\n[{"statement": "Fact", "confidence": 0.8}]\n```'

        with patch(
            "research_tool.agent.nodes.process.get_llm_router"
        ) as mock_get_router:
            mock_router = AsyncMock()
            mock_router.complete = AsyncMock(return_value=mock_response)
            mock_get_router.return_value = mock_router

            result = await extract_facts_with_llm(
                "Content here",
                "http://test.com",
                "query"
            )

            assert len(result) == 1


class TestDeduplicateFacts:
    """Test suite for deduplicate_facts function."""

    def test_dedupe_removes_exact_duplicates(self) -> None:
        """deduplicate_facts removes exact duplicate statements."""
        facts = [
            {"statement": "Same fact", "source": "url1", "confidence": 0.8},
            {"statement": "Same fact", "source": "url2", "confidence": 0.9},
        ]
        result = deduplicate_facts(facts)
        assert len(result) == 1

    def test_dedupe_keeps_unique_facts(self) -> None:
        """deduplicate_facts keeps unique statements."""
        facts = [
            {"statement": "Fact one", "source": "url1", "confidence": 0.8},
            {"statement": "Fact two", "source": "url2", "confidence": 0.9},
        ]
        result = deduplicate_facts(facts)
        assert len(result) == 2

    def test_dedupe_case_insensitive(self) -> None:
        """deduplicate_facts is case-insensitive."""
        facts = [
            {"statement": "Same Fact", "source": "url1", "confidence": 0.8},
            {"statement": "same fact", "source": "url2", "confidence": 0.9},
        ]
        result = deduplicate_facts(facts)
        assert len(result) == 1

    def test_dedupe_handles_empty_list(self) -> None:
        """deduplicate_facts handles empty list."""
        result = deduplicate_facts([])
        assert result == []
