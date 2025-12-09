"""Source selection decision tree from META guide Section 7.2."""


from research_tool.core.logging import get_logger
from research_tool.models.domain import DomainConfiguration

logger = get_logger(__name__)


def select_sources_for_query(
    query: str,
    domain: str | None,
    domain_config: DomainConfiguration | None,
    source_effectiveness: dict[str, float] | None = None,
    known_failures: set[str] | None = None
) -> list[str]:
    """Select and order sources for a research query.

    Implements META guide Section 7.2 Source Selection Decision Tree:
    1. If domain recognized → use domain config + effectiveness scores
    2. If novel domain → use meta-search to discover sources
    3. If partially recognized → use closest match + general sources

    Args:
        query: Research query
        domain: Recognized domain (if any)
        domain_config: Domain configuration (if domain recognized)
        source_effectiveness: Effectiveness scores for sources (0.0-1.0)
        known_failures: Set of sources known to fail for this query pattern

    Returns:
        list[str]: Ordered list of source names to query
    """
    logger.info(
        "source_selection_start",
        domain=domain,
        has_config=domain_config is not None
    )

    source_effectiveness = source_effectiveness or {}
    known_failures = known_failures or set()

    # Decision tree: Is query domain recognized?
    if domain and domain_config:
        # YES - Load domain configuration and sort by effectiveness
        sources = _select_from_domain_config(
            domain_config,
            source_effectiveness,
            known_failures
        )
        logger.info(
            "source_selection_domain_recognized",
            domain=domain,
            sources=sources
        )
        return sources

    # NO - Domain not recognized
    if _is_novel_domain(query, domain):
        # Completely novel domain - use meta-search
        sources = _select_for_novel_domain(query, known_failures)
        logger.info(
            "source_selection_novel_domain",
            query=query,
            sources=sources
        )
        return sources

    # Partially recognized - use general sources
    sources = _select_general_sources(known_failures)
    logger.info(
        "source_selection_general",
        sources=sources
    )
    return sources


def _select_from_domain_config(
    domain_config: DomainConfiguration,
    source_effectiveness: dict[str, float],
    known_failures: set[str]
) -> list[str]:
    """Select sources from domain config, sorted by priority * effectiveness.

    Args:
        domain_config: Domain configuration with primary/secondary sources
        source_effectiveness: Effectiveness scores (0.0-1.0)
        known_failures: Sources to exclude

    Returns:
        list[str]: Ordered source names
    """
    # Build priority map: primary sources = 1.0, secondary = 0.5
    source_priorities: dict[str, float] = {}
    for source in domain_config.primary_sources:
        source_priorities[source] = 1.0
    for source in domain_config.secondary_sources:
        source_priorities[source] = 0.5

    # Calculate composite score: priority * effectiveness
    scored_sources: list[tuple[str, float]] = []
    for source_name, priority in source_priorities.items():
        # Skip known failures
        if source_name in known_failures:
            logger.debug(
                "source_skipped_known_failure",
                source=source_name
            )
            continue

        # Skip excluded sources
        if source_name in domain_config.excluded_sources:
            logger.debug(
                "source_skipped_excluded",
                source=source_name
            )
            continue

        # Get effectiveness (default to 0.5 if unknown)
        effectiveness = source_effectiveness.get(source_name, 0.5)

        # Composite score
        score = priority * effectiveness
        scored_sources.append((source_name, score))

    # Sort by score (highest first)
    scored_sources.sort(key=lambda x: x[1], reverse=True)

    return [source for source, _ in scored_sources]


def _is_novel_domain(query: str, domain: str | None) -> bool:
    """Check if domain is completely novel (no partial match).

    Args:
        query: Research query
        domain: Detected domain (if any)

    Returns:
        bool: True if completely novel
    """
    # If no domain detected at all, it's novel
    if domain is None:
        return True

    # If domain is "unknown" or "general", it's novel
    return domain.lower() in ("unknown", "general", "other")


def _select_for_novel_domain(
    query: str,
    known_failures: set[str]
) -> list[str]:
    """Select sources for novel domain using meta-search strategy.

    For novel domains, we:
    1. Use general-purpose search first (Tavily, Exa)
    2. Add academic sources as fallback
    3. Note: Full meta-search "how to research [domain]" is Phase 5

    Args:
        query: Research query
        known_failures: Sources to exclude

    Returns:
        list[str]: Ordered source names
    """
    # Phase 4: Use general sources
    # Phase 5 will implement actual meta-search
    general_sources = [
        "tavily",
        "exa",
        "brave",
        "semantic_scholar",
        "arxiv",
        "pubmed"
    ]

    # Filter out known failures
    sources = [s for s in general_sources if s not in known_failures]

    logger.debug(
        "novel_domain_sources_selected",
        query=query,
        source_count=len(sources)
    )

    return sources


def _select_general_sources(known_failures: set[str]) -> list[str]:
    """Select general-purpose sources for partially recognized domains.

    Args:
        known_failures: Sources to exclude

    Returns:
        list[str]: Ordered source names
    """
    # General-purpose sources in priority order
    general_sources = [
        "tavily",      # Fast general web search
        "exa",         # Semantic search
        "brave",       # Privacy-focused search
        "semantic_scholar",  # Academic papers
        "arxiv",       # Preprints
        "pubmed",      # Medical research
    ]

    # Filter out known failures
    sources = [s for s in general_sources if s not in known_failures]

    return sources


def should_skip_source(
    source_name: str,
    url_pattern: str | None,
    known_failures: dict[str, set[str]] | None = None
) -> bool:
    """Check if source is known to fail for URL pattern.

    Args:
        source_name: Source to check
        url_pattern: URL pattern (e.g., "*.pdf", "arxiv.org/*")
        known_failures: Dict mapping source_name to set of failing patterns

    Returns:
        bool: True if should skip this source
    """
    if not known_failures or not url_pattern:
        return False

    failing_patterns = known_failures.get(source_name, set())

    # Simple pattern matching (can be enhanced in Phase 5)
    for pattern in failing_patterns:
        if pattern in url_pattern:
            logger.debug(
                "source_skipped_pattern_match",
                source=source_name,
                pattern=pattern,
                url=url_pattern
            )
            return True

    return False
