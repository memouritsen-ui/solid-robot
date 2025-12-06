"""Collection node - query sources per plan."""

from contextlib import suppress
from datetime import datetime

from research_tool.core.logging import get_logger
from research_tool.models.domain import DomainConfiguration
from research_tool.models.state import ResearchState
from research_tool.services.search.arxiv import ArxivProvider
from research_tool.services.search.brave import BraveProvider
from research_tool.services.search.pubmed import PubMedProvider
from research_tool.services.search.semantic_scholar import SemanticScholarProvider
from research_tool.services.search.tavily import TavilyProvider

logger = get_logger(__name__)


async def collect_node(state: ResearchState) -> dict:
    """Collect data from sources per research plan.

    Anti-pattern prevention:
    - Use ranked sources (Anti-Pattern #5)
    - Handle obstacles gracefully (Anti-Pattern #6)

    Args:
        state: Current research state

    Returns:
        dict: State updates with new sources queried
    """
    logger.info("collect_node_start")

    refined_query = state.get("refined_query", state["original_query"])
    domain = state.get("domain", "general")

    # Get domain configuration
    if domain == "medical":
        config = DomainConfiguration.for_medical()
    elif domain == "competitive_intelligence":
        config = DomainConfiguration.for_competitive_intelligence()
    elif domain == "academic":
        config = DomainConfiguration.for_academic()
    else:
        config = DomainConfiguration.default()

    # Initialize providers
    providers = {}
    with suppress(ValueError):  # Not configured
        providers["tavily"] = TavilyProvider()

    providers["semantic_scholar"] = SemanticScholarProvider()
    providers["pubmed"] = PubMedProvider()
    providers["arxiv"] = ArxivProvider()

    with suppress(ValueError):  # Not configured
        providers["brave"] = BraveProvider()

    # Query primary sources first
    sources_queried = []
    all_results = []

    for source_name in config.primary_sources:
        if source_name in providers:
            provider = providers[source_name]
            if await provider.is_available():
                try:
                    results = await provider.search(refined_query, max_results=10)
                    sources_queried.append(source_name)
                    all_results.extend(results)
                    logger.info(
                        "source_queried",
                        source=source_name,
                        results_count=len(results)
                    )
                except Exception as e:
                    logger.error(
                        "source_query_failed",
                        source=source_name,
                        error=str(e)
                    )

    logger.info("collect_node_complete", sources_queried=len(sources_queried))

    # Convert results to entities (simplified)
    entities_found = []
    for result in all_results[:20]:  # Limit for now
        entities_found.append({
            "url": result.get("url"),
            "title": result.get("title"),
            "source": result.get("source_name"),
            "retrieved_at": datetime.now().isoformat()
        })

    return {
        "sources_queried": sources_queried,
        "entities_found": entities_found,
        "current_phase": "collect"
    }
