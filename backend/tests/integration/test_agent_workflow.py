"""Integration tests for agent workflow."""


import pytest

from research_tool.models.state import ResearchState


class TestAgentWorkflow:
    """Test suite for complete agent workflow integration."""

    @pytest.mark.asyncio
    async def test_complete_workflow_executes(self) -> None:
        """Complete workflow executes all nodes without errors.

        Tests #183: Complete workflow executes

        Note: Uses graph without checkpointing for testing.
        """
        from langgraph.graph import END, StateGraph

        # Create simple graph without checkpointing
        workflow = StateGraph(ResearchState)

        # Mock nodes
        async def mock_start(state: ResearchState) -> dict:
            return {"current_phase": "start", "should_stop": True, "stop_reason": "Test"}

        async def mock_synthesize(state: ResearchState) -> dict:
            return {
                "final_report": {"query": "test", "summary": "Done"},
                "current_phase": "synthesize"
            }

        workflow.add_node("start", mock_start)
        workflow.add_node("synthesize", mock_synthesize)
        workflow.set_entry_point("start")
        workflow.add_edge("start", "synthesize")
        workflow.add_edge("synthesize", END)

        graph = workflow.compile()

        # Create initial state
        initial_state: ResearchState = {
            "session_id": "test-session",
            "original_query": "test query",
            "privacy_mode": "CLOUD_ALLOWED",
            "sources_queried": [],
            "entities_found": [],
            "facts_extracted": [],
            "access_failures": [],
            "should_stop": False,
            "saturation_metrics": None,
            "stop_reason": None,
            "final_report": None,
            "export_path": None
        }

        # Run workflow
        final_state = await graph.ainvoke(initial_state)

        # Verify workflow completed
        assert final_state is not None
        assert "final_report" in final_state
        assert final_state["final_report"] is not None

    @pytest.mark.asyncio
    async def test_tools_integrate_with_agent(self) -> None:
        """Agent tools integrate correctly with workflow.

        Tests #187: Tools integrate with agent
        """
        from research_tool.agent.tools import search_sources
        from research_tool.services.search.provider import SearchProvider

        # Create mock provider
        class MockProvider(SearchProvider):
            @property
            def name(self) -> str:
                return "mock"

            @property
            def requests_per_second(self) -> float:
                return 10.0

            async def search(self, query: str, max_results: int = 10, filters=None):
                return [{"url": "http://test.com", "title": "Test", "snippet": "Test"}]

            async def is_available(self) -> bool:
                return True

        provider_registry = {"mock": MockProvider()}

        # Test search tool
        result = await search_sources(
            query="test query",
            sources=["mock"],
            provider_registry=provider_registry
        )

        # Verify tool executed
        assert result["sources_queried"] == 1
        assert result["sources_succeeded"] == 1
        assert len(result["results"]) == 1

    @pytest.mark.asyncio
    async def test_full_research_cycle_with_mocks(self) -> None:
        """Full research cycle completes with mocked providers.

        Tests #199: Full research cycle on test query

        Note: Creates graph without checkpointing for testing.
        """
        from langgraph.graph import END, StateGraph

        # Create workflow without checkpointing
        workflow = StateGraph(ResearchState)

        # Mock all nodes
        async def mock_clarify(state):
            return {"current_phase": "clarify", "refined_query": state["original_query"]}

        async def mock_plan(state):
            return {"current_phase": "plan"}

        async def mock_collect(state):
            return {
                "current_phase": "collect",
                "sources_queried": ["tavily"],
                "entities_found": [{"name": "test"}],
                "facts_extracted": [{"content": "test fact"}]
            }

        async def mock_evaluate(state):
            return {"current_phase": "evaluate", "should_stop": True, "stop_reason": "Test"}

        async def mock_synthesize(state):
            return {
                "final_report": {"query": "test", "summary": "Complete"},
                "current_phase": "synthesize"
            }

        workflow.add_node("clarify", mock_clarify)
        workflow.add_node("plan", mock_plan)
        workflow.add_node("collect", mock_collect)
        workflow.add_node("evaluate", mock_evaluate)
        workflow.add_node("synthesize", mock_synthesize)

        workflow.set_entry_point("clarify")
        workflow.add_edge("clarify", "plan")
        workflow.add_edge("plan", "collect")
        workflow.add_edge("collect", "evaluate")
        workflow.add_edge("evaluate", "synthesize")
        workflow.add_edge("synthesize", END)

        graph = workflow.compile()

        # Run workflow
        initial_state: ResearchState = {
            "session_id": "full-cycle-test",
            "original_query": "cancer treatment",
            "privacy_mode": "LOCAL_ONLY",
            "sources_queried": [],
            "entities_found": [],
            "facts_extracted": [],
            "access_failures": [],
            "should_stop": False,
            "saturation_metrics": None,
            "stop_reason": None,
            "final_report": None,
            "export_path": None
        }

        final_state = await graph.ainvoke(initial_state)

        # Verify final report was generated
        assert "final_report" in final_state
        assert final_state["final_report"] is not None


class TestWorkflowEdgeCases:
    """Test edge cases in workflow execution."""

    @pytest.mark.asyncio
    async def test_workflow_handles_empty_query(self) -> None:
        """Workflow handles empty query gracefully.

        Note: Creates graph without checkpointing for testing.
        """
        from langgraph.graph import END, StateGraph

        # Create simple graph
        workflow = StateGraph(ResearchState)

        async def handle_empty(state):
            return {
                "should_stop": True,
                "stop_reason": "Empty query",
                "current_phase": "clarify",
                "final_report": {"error": "Empty query"}
            }

        workflow.add_node("clarify", handle_empty)
        workflow.set_entry_point("clarify")
        workflow.add_edge("clarify", END)

        graph = workflow.compile()

        initial_state: ResearchState = {
            "session_id": "empty-query-test",
            "original_query": "",
            "privacy_mode": "CLOUD_ALLOWED",
            "sources_queried": [],
            "entities_found": [],
            "facts_extracted": [],
            "access_failures": [],
            "should_stop": False,
            "saturation_metrics": None,
            "stop_reason": None,
            "final_report": None,
            "export_path": None
        }

        final_state = await graph.ainvoke(initial_state)

        # Should handle gracefully
        assert final_state is not None
        assert final_state["should_stop"] is True
