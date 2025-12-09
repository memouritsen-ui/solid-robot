"""LangGraph research workflow definition."""

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from research_tool.models.state import ResearchState

from .nodes import (
    analyze_node,
    clarify_node,
    collect_node,
    evaluate_node,
    plan_node,
    process_node,
    synthesize_node,
)


def should_continue_research(state: ResearchState) -> str:
    """Decide whether to continue collecting or stop and synthesize.

    Args:
        state: Current research state

    Returns:
        str: "continue" to collect more, "stop" to synthesize
    """
    if state.get("should_stop", False):
        return "stop"
    return "continue"


def create_research_graph():  # type: ignore[no-untyped-def]
    """Create the research workflow graph.

    Workflow:
    1. Clarify query and detect domain
    2. Plan research using memory
    3. Collect data from sources
    4. Process to extract entities/facts
    5. Analyze for verification
    6. Evaluate saturation
    7. If not saturated → go back to collect
    8. If saturated → synthesize report

    Returns:
        Compiled LangGraph workflow
    """
    # Initialize graph with state type
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("collect", collect_node)
    workflow.add_node("process", process_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("synthesize", synthesize_node)

    # Define linear edges
    workflow.set_entry_point("clarify")
    workflow.add_edge("clarify", "plan")
    workflow.add_edge("plan", "collect")
    workflow.add_edge("collect", "process")
    workflow.add_edge("process", "analyze")
    workflow.add_edge("analyze", "evaluate")

    # Conditional edge: evaluate → continue collecting or stop
    workflow.add_conditional_edges(
        "evaluate",
        should_continue_research,
        {
            "continue": "collect",  # Loop back for more data
            "stop": "synthesize"    # Saturation reached
        }
    )

    workflow.add_edge("synthesize", END)

    # Add checkpointing for resumability
    with SqliteSaver.from_conn_string("./data/checkpoints.db") as checkpointer:
        return workflow.compile(checkpointer=checkpointer)
