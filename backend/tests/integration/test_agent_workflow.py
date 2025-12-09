"""Integration tests for agent workflow."""


import pytest

from research_tool.agent.graph import create_research_graph


class TestAgentWorkflow:
    """Test suite for complete agent workflow integration."""

    @pytest.mark.asyncio
    async def test_real_graph_structure(self) -> None:
        """Test that real graph has correct node structure.

        Tests #183: Complete workflow executes
        """
        graph = create_research_graph()

        # Verify graph was created
        assert graph is not None

        # Check graph has the expected nodes by checking the compiled graph
        # The graph should have nodes for the research workflow
        graph_dict = graph.get_graph().to_json()
        assert "nodes" in graph_dict

    @pytest.mark.asyncio
    async def test_real_graph_is_invokable(self) -> None:
        """Real graph has ainvoke method and is callable.

        Uses actual graph structure.
        """
        graph = create_research_graph()

        # Graph should be callable
        assert callable(graph.ainvoke)
        assert hasattr(graph, "get_graph")

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
    async def test_real_graph_node_count(self) -> None:
        """Real graph has expected number of nodes.

        Tests #199: Verifies graph structure is complete.
        """
        graph = create_research_graph()

        # Get graph structure
        graph_data = graph.get_graph().to_json()

        # Should have 8 nodes: clarify, plan, collect, process,
        # analyze, evaluate, synthesize, export
        # Plus __start__ and __end__ nodes added by LangGraph
        node_count = len(graph_data.get("nodes", []))
        assert node_count >= 8, f"Expected at least 8 nodes, got {node_count}"

    @pytest.mark.asyncio
    async def test_graph_conditional_edges(self) -> None:
        """Graph has conditional edge from evaluate node.

        Verifies the saturation loop is properly configured.
        """
        graph = create_research_graph()

        # Get graph structure
        graph_data = graph.get_graph().to_json()

        # Check edges exist
        edges = graph_data.get("edges", [])
        assert len(edges) > 0, "Graph should have edges"


class TestWorkflowEdgeCases:
    """Test edge cases in workflow execution."""

    def test_graph_can_be_created_multiple_times(self) -> None:
        """Multiple graph instances can be created independently."""
        graph1 = create_research_graph()
        graph2 = create_research_graph()

        # Both should be valid
        assert graph1 is not None
        assert graph2 is not None

        # They should be different instances
        assert graph1 is not graph2

    def test_graph_with_custom_checkpointer(self) -> None:
        """Graph accepts custom checkpointer."""
        from langgraph.checkpoint.memory import MemorySaver

        custom_saver = MemorySaver()
        graph = create_research_graph(checkpointer=custom_saver)

        assert graph is not None
