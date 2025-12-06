"""Saturation detection from META guide Section 3.7 and 7.5."""

from dataclasses import asdict, dataclass


@dataclass
class SaturationMetrics:
    """Metrics for determining research saturation.

    Thresholds from META guide:
    - new_entities_ratio < 0.05 → stop
    - new_facts_ratio < 0.05 → stop
    - source_coverage > 0.95 → stop
    - citation_circularity > 0.80 → stop
    """

    new_entities_ratio: float      # New entities / Total entities
    new_facts_ratio: float         # New facts / Total facts
    citation_circularity: float    # Self-referencing citation ratio
    source_coverage: float         # Sources queried / Available sources

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


def calculate_saturation(
    entities_before: int,
    entities_after: int,
    facts_before: int,
    facts_after: int,
    circular_citations: int,
    total_citations: int,
    sources_queried: int,
    sources_available: int
) -> SaturationMetrics:
    """Calculate saturation metrics.

    Args:
        entities_before: Entity count before this cycle
        entities_after: Entity count after this cycle
        facts_before: Fact count before this cycle
        facts_after: Fact count after this cycle
        circular_citations: Number of self-referencing citations
        total_citations: Total citation count
        sources_queried: Number of sources queried
        sources_available: Total number of available sources

    Returns:
        SaturationMetrics: Calculated metrics
    """
    new_entities = entities_after - entities_before
    new_facts = facts_after - facts_before

    return SaturationMetrics(
        new_entities_ratio=new_entities / max(entities_after, 1),
        new_facts_ratio=new_facts / max(facts_after, 1),
        citation_circularity=circular_citations / max(total_citations, 1),
        source_coverage=sources_queried / max(sources_available, 1)
    )


def should_stop(metrics: SaturationMetrics) -> tuple[bool, str]:
    """Determine if research should stop based on saturation metrics.

    Decision tree from META guide Section 7.5:
    - Stop if new_entities_ratio < 0.05 (entity saturation)
    - Stop if new_facts_ratio < 0.05 (fact saturation)
    - Stop if source_coverage > 0.95 (sources exhausted)
    - Stop if citation_circularity > 0.80 (circular references)
    - Continue otherwise

    Args:
        metrics: Saturation metrics

    Returns:
        tuple[bool, str]: (should_stop, reason_in_plain_language)
    """
    # Check entity saturation
    if metrics.new_entities_ratio < 0.05:
        return True, (
            f"Entity saturation reached: Only {metrics.new_entities_ratio:.1%} "
            "of entities found in last cycle were new (<5% threshold)"
        )

    # Check fact saturation
    if metrics.new_facts_ratio < 0.05:
        return True, (
            f"Fact saturation reached: Only {metrics.new_facts_ratio:.1%} "
            "of facts found in last cycle were new (<5% threshold)"
        )

    # Check source coverage
    if metrics.source_coverage > 0.95:
        return True, (
            f"Source coverage complete: {metrics.source_coverage:.1%} "
            "of available sources have been queried (>95% threshold)"
        )

    # Check citation circularity
    if metrics.citation_circularity > 0.80:
        return True, (
            f"High citation circularity: {metrics.citation_circularity:.1%} "
            "of citations are circular/self-referencing (>80% threshold)"
        )

    # Not saturated - continue research
    return False, (
        f"Saturation not yet reached: {metrics.new_entities_ratio:.1%} new entities, "
        f"{metrics.new_facts_ratio:.1%} new facts, "
        f"{metrics.source_coverage:.1%} source coverage"
    )
