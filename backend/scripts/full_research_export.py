#!/usr/bin/env python3
"""Run research and export ALL data to JSON."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from research_tool.agent.graph import create_research_graph
from research_tool.services.llm.selector import PrivacyMode


async def run_full_research(query: str, output_path: Path) -> dict:
    """Run research and capture ALL data."""

    graph = create_research_graph()

    initial_state = {
        "session_id": f"full-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "original_query": query,
        "privacy_mode": PrivacyMode.CLOUD_ALLOWED,
        "started_at": datetime.now().isoformat(),
        "current_phase": "starting",
        "sources_queried": [],
        "entities_found": [],
        "facts_extracted": [],
        "access_failures": [],
        "should_stop": False,
        "saturation_metrics": None,
        "stop_reason": None,
        "final_report": None,
        "export_path": None,
    }

    session_id = initial_state["session_id"]
    print(f"Starting research: {query}")
    print(f"Session ID: {session_id}")
    print("-" * 60)

    # Run the graph with thread_id config
    config = {"configurable": {"thread_id": session_id}}
    final_state = await graph.ainvoke(initial_state, config=config)

    # Prepare full export
    full_export = {
        "query": query,
        "session_id": final_state.get("session_id"),
        "generated_at": datetime.now().isoformat(),
        "domain": final_state.get("domain"),

        # ALL entities (raw search results)
        "entities": final_state.get("entities_found", []),
        "entity_count": len(final_state.get("entities_found", [])),

        # ALL extracted facts
        "facts": final_state.get("facts_extracted", []),
        "fact_count": len(final_state.get("facts_extracted", [])),

        # Sources
        "sources_queried": final_state.get("sources_queried", []),

        # Failures
        "access_failures": final_state.get("access_failures", []),

        # Saturation metrics
        "saturation_metrics": final_state.get("saturation_metrics"),
        "stop_reason": final_state.get("stop_reason"),

        # Final report (synthesized)
        "final_report": final_state.get("final_report"),
    }

    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(full_export, f, indent=2, default=str)

    print(f"\nExport complete!")
    print(f"  Entities: {full_export['entity_count']}")
    print(f"  Facts: {full_export['fact_count']}")
    print(f"  Saved to: {output_path}")

    return full_export


if __name__ == "__main__":
    query = "EU drone logistics startups and companies 2024"
    output = Path("data/reports/full_drone_research.json")

    asyncio.run(run_full_research(query, output))
