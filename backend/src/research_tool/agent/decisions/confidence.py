"""Confidence scoring system for research facts.

Implements Phase 5 intelligence feature for:
- Source-based confidence (quality and quantity of sources)
- Verification-based confidence (contradictions and verification status)
- Composite confidence scoring with explanations
"""

import math
from dataclasses import asdict, dataclass
from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.entities import Fact

logger = get_logger(__name__)


# Source quality definitions
SOURCE_QUALITY_MAP: dict[str, dict[str, Any]] = {
    # Academic/peer-reviewed sources
    "pubmed": {
        "credibility": 0.9,
        "is_peer_reviewed": True,
        "is_primary_source": True,
    },
    "semantic_scholar": {
        "credibility": 0.85,
        "is_peer_reviewed": True,
        "is_primary_source": True,
    },
    "arxiv": {
        "credibility": 0.7,
        "is_peer_reviewed": False,  # Preprints
        "is_primary_source": True,
    },
    # General search sources
    "tavily": {
        "credibility": 0.5,
        "is_peer_reviewed": False,
        "is_primary_source": False,
    },
    "exa": {
        "credibility": 0.55,
        "is_peer_reviewed": False,
        "is_primary_source": False,
    },
    "brave": {
        "credibility": 0.5,
        "is_peer_reviewed": False,
        "is_primary_source": False,
    },
    # Specialized sources
    "unpaywall": {
        "credibility": 0.8,
        "is_peer_reviewed": True,
        "is_primary_source": True,
    },
    "playwright_crawler": {
        "credibility": 0.4,
        "is_peer_reviewed": False,
        "is_primary_source": False,
    },
}


@dataclass
class SourceQuality:
    """Quality metrics for a source.

    Attributes:
        source_name: Name of the source
        credibility: Base credibility score (0.0-1.0)
        is_peer_reviewed: Whether source is peer-reviewed
        is_primary_source: Whether source is primary/original
        recency_score: How recent the source is (0.0-1.0)
    """

    source_name: str
    credibility: float
    is_peer_reviewed: bool
    is_primary_source: bool
    recency_score: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CompositeConfidence:
    """Composite confidence score with breakdown.

    Attributes:
        source_confidence: Confidence from source quality/quantity
        verification_confidence: Confidence from verification status
        composite_score: Combined weighted score
        explanation: Human-readable explanation
    """

    source_confidence: float
    verification_confidence: float
    composite_score: float
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


def get_source_quality(source_name: str) -> SourceQuality:
    """Get quality metrics for a source.

    Args:
        source_name: Name of the source

    Returns:
        SourceQuality with quality metrics
    """
    # Normalize source name
    normalized = source_name.lower().replace("-", "_").replace(" ", "_")

    # Check for known sources
    if normalized in SOURCE_QUALITY_MAP:
        data = SOURCE_QUALITY_MAP[normalized]
        return SourceQuality(
            source_name=source_name,
            credibility=data["credibility"],
            is_peer_reviewed=data["is_peer_reviewed"],
            is_primary_source=data["is_primary_source"],
        )

    # Default for unknown sources
    logger.debug("unknown_source_quality", source=source_name)
    return SourceQuality(
        source_name=source_name,
        credibility=0.3,
        is_peer_reviewed=False,
        is_primary_source=False,
    )


def calculate_source_confidence(sources: list[str]) -> float:
    """Calculate confidence based on source quality and quantity.

    Factors:
    - Number of sources (more = higher confidence)
    - Quality of sources (academic > general web)
    - Peer-review status

    Args:
        sources: List of source names or URLs

    Returns:
        Confidence score (0.0-1.0)
    """
    if not sources:
        return 0.0

    # Extract source names from URLs if needed
    source_names = []
    for source in sources:
        if "/" in source:
            # It's a URL, try to extract source name
            source_names.append(_extract_source_from_url(source))
        else:
            source_names.append(source)

    # Calculate quality scores
    qualities = [get_source_quality(s) for s in source_names]

    # Average credibility
    avg_credibility = sum(q.credibility for q in qualities) / len(qualities)

    # Bonus for peer-reviewed sources
    peer_reviewed_count = sum(1 for q in qualities if q.is_peer_reviewed)
    peer_review_bonus = min(0.2, peer_reviewed_count * 0.05)

    # Bonus for multiple sources (logarithmic)
    source_count_bonus = min(0.3, 0.1 * math.log2(len(sources) + 1))

    # Calculate final confidence
    confidence = avg_credibility + peer_review_bonus + source_count_bonus

    # Cap at 1.0
    return min(1.0, confidence)


def _extract_source_from_url(url: str) -> str:
    """Extract source name from URL.

    Args:
        url: Source URL

    Returns:
        Source name
    """
    url_lower = url.lower()

    # Check for known domains
    if "pubmed" in url_lower or "ncbi.nlm.nih" in url_lower:
        return "pubmed"
    elif "semanticscholar" in url_lower:
        return "semantic_scholar"
    elif "arxiv" in url_lower:
        return "arxiv"
    elif "unpaywall" in url_lower:
        return "unpaywall"

    # Default: unknown web source
    return "web"


def calculate_verification_confidence(fact: Fact) -> float:
    """Calculate confidence based on verification status.

    Factors:
    - Verified status
    - Number of contradictions
    - Existing confidence score

    Args:
        fact: Fact to calculate confidence for

    Returns:
        Verification confidence (0.0-1.0)
    """
    base_confidence = fact.confidence

    # Boost for verified facts
    if fact.verified:
        base_confidence = min(1.0, base_confidence + 0.15)

    # Penalty for contradictions
    contradiction_count = len(fact.contradictions)
    if contradiction_count > 0:
        # Each contradiction reduces confidence
        penalty = min(0.5, contradiction_count * 0.15)
        base_confidence = max(0.1, base_confidence - penalty)

    return base_confidence


def calculate_composite_confidence(fact: Fact) -> CompositeConfidence:
    """Calculate composite confidence score for a fact.

    Combines source-based and verification-based confidence
    with a weighted average.

    Args:
        fact: Fact to calculate confidence for

    Returns:
        CompositeConfidence with breakdown and explanation
    """
    # Calculate component confidences
    source_conf = calculate_source_confidence(fact.sources)
    verification_conf = calculate_verification_confidence(fact)

    # Weighted average (source: 40%, verification: 60%)
    # Verification is weighted higher as it accounts for contradictions
    composite = 0.4 * source_conf + 0.6 * verification_conf

    # Generate explanation
    explanation = _generate_confidence_explanation(
        fact, source_conf, verification_conf
    )

    logger.debug(
        "composite_confidence_calculated",
        source_conf=source_conf,
        verification_conf=verification_conf,
        composite=composite
    )

    return CompositeConfidence(
        source_confidence=source_conf,
        verification_confidence=verification_conf,
        composite_score=composite,
        explanation=explanation
    )


def _generate_confidence_explanation(
    fact: Fact,
    source_conf: float,
    verification_conf: float
) -> str:
    """Generate human-readable explanation for confidence score.

    Args:
        fact: The fact being scored
        source_conf: Source confidence score
        verification_conf: Verification confidence score

    Returns:
        Explanation string
    """
    parts = []

    # Source explanation
    source_count = len(fact.sources)
    if source_count == 0:
        parts.append("No sources provided")
    elif source_count == 1:
        parts.append("Based on 1 source")
    else:
        parts.append(f"Based on {source_count} sources")

    # Check for peer-reviewed
    qualities = [get_source_quality(s) for s in fact.sources]
    peer_reviewed_count = sum(1 for q in qualities if q.is_peer_reviewed)
    if peer_reviewed_count > 0:
        parts.append(f"{peer_reviewed_count} peer-reviewed")

    # Verification status
    if fact.verified:
        parts.append("verified")
    else:
        parts.append("not verified")

    # Contradictions
    if fact.contradictions:
        parts.append(f"{len(fact.contradictions)} contradiction(s) found")

    return ", ".join(parts)
