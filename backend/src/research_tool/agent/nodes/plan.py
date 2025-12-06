"""Planning node - create research plan using memory."""

from research_tool.core.logging import get_logger
from research_tool.models.domain import DomainConfiguration
from research_tool.models.state import ResearchState
from research_tool.services.memory import CombinedMemoryRepository

logger = get_logger(__name__)


async def plan_node(state: ResearchState) -> dict:
    """Create research plan using memory and domain configuration.

    Anti-pattern prevention: Use memory for planning (Anti-Pattern #8)

    Args:
        state: Current research state

    Returns:
        dict: State updates
    """
    logger.info("plan_node_start", domain=state.get("domain"))

    # Get domain configuration
    domain = state.get("domain", "general")
    if domain == "medical":
        config = DomainConfiguration.for_medical()
    elif domain == "competitive_intelligence":
        config = DomainConfiguration.for_competitive_intelligence()
    elif domain == "academic":
        config = DomainConfiguration.for_academic()
    elif domain == "regulatory":
        config = DomainConfiguration.for_regulatory()
    else:
        config = DomainConfiguration.default()

    # Initialize memory repository
    memory = CombinedMemoryRepository()
    await memory.initialize()

    # Check for similar past research
    refined_query = state.get("refined_query", state["original_query"])
    past_research = await memory.search_similar(refined_query, limit=3)

    # Get ranked sources for this domain
    all_sources = config.primary_sources + config.secondary_sources
    ranked_sources = await memory.get_ranked_sources(domain, all_sources)

    # Get known failures to avoid
    failed_urls = await memory.get_failed_urls()

    logger.info(
        "plan_node_complete",
        primary_sources=config.primary_sources,
        ranked_sources=[s[0] for s in ranked_sources[:5]],
        past_research_found=len(past_research),
        known_failures=len(failed_urls)
    )

    # Store plan in state (simplified - full version would be more detailed)
    return {
        "current_phase": "plan",
        # Plan metadata stored but not part of typed state
    }
