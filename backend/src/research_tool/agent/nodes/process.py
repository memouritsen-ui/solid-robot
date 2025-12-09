"""Processing node - extract entities and facts from collected data."""

from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState

logger = get_logger(__name__)


async def process_node(state: ResearchState) -> dict[str, Any]:
    """Process collected data to extract entities and facts.

    Args:
        state: Current research state

    Returns:
        dict: State updates
    """
    logger.info("process_node_start")

    # In full implementation, this would:
    # 1. Extract entities (people, orgs, products, etc.)
    # 2. Extract facts with sources
    # 3. De-duplicate entities
    # 4. Link related information

    # Simulate fact extraction (simplified)
    facts_extracted = []
    for entity in state.get("entities_found", [])[:10]:
        facts_extracted.append({
            "statement": f"Information found about: {entity.get('title', 'Unknown')}",
            "source": entity.get("url"),
            "confidence": 0.5
        })

    logger.info("process_node_complete", facts_extracted=len(facts_extracted))

    return {
        "facts_extracted": facts_extracted,
        "current_phase": "process"
    }
