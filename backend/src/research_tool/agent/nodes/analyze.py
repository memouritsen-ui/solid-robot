"""Analysis node - cross-verify facts, detect contradictions, score confidence."""

import re
from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState

logger = get_logger(__name__)


async def cross_reference_facts(
    facts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Group facts that discuss the same topic/claim.

    Uses text similarity to find facts making similar claims,
    which can then be used to boost confidence.

    Args:
        facts: List of extracted facts

    Returns:
        List of fact groups with agreement scores
    """
    if not facts:
        return []

    # Simple word-based similarity grouping
    groups: list[dict[str, Any]] = []
    used_indices: set[int] = set()

    for i, fact1 in enumerate(facts):
        if i in used_indices:
            continue

        group_facts = [fact1]
        statement1 = fact1.get("statement", "").lower()
        words1 = set(re.findall(r"\b\w+\b", statement1))

        for j, fact2 in enumerate(facts[i + 1 :], start=i + 1):
            if j in used_indices:
                continue

            statement2 = fact2.get("statement", "").lower()
            words2 = set(re.findall(r"\b\w+\b", statement2))

            # Calculate Jaccard similarity
            if words1 and words2:
                intersection = len(words1 & words2)
                union = len(words1 | words2)
                similarity = intersection / union

                # Group if similarity > 0.4
                if similarity > 0.4:
                    group_facts.append(fact2)
                    used_indices.add(j)

        used_indices.add(i)

        # Calculate agreement score based on source diversity
        unique_sources = {f.get("source", "") for f in group_facts}
        agreement_score = min(1.0, len(unique_sources) / 3)  # 3+ sources = 1.0

        groups.append({
            "facts": group_facts,
            "fact_count": len(group_facts),
            "unique_sources": list(unique_sources),
            "agreement_score": agreement_score
        })

    return groups


async def detect_contradictions(
    facts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Detect contradicting facts.

    Looks for facts that make conflicting claims about:
    - Dates/years
    - Numbers/amounts
    - Boolean states (is/is not)

    Args:
        facts: List of extracted facts

    Returns:
        List of contradiction pairs with details
    """
    contradictions: list[dict[str, Any]] = []

    # Patterns for extractable values
    year_pattern = r"\b(19|20)\d{2}\b"
    number_pattern = r"\b\d+(?:\.\d+)?(?:%|billion|million|thousand)?\b"

    for i, fact1 in enumerate(facts):
        stmt1 = fact1.get("statement", "")

        for fact2 in facts[i + 1 :]:
            # Skip same source
            if fact1.get("source") == fact2.get("source"):
                continue

            stmt2 = fact2.get("statement", "")

            # Check for year contradictions
            years1 = set(re.findall(year_pattern, stmt1))
            years2 = set(re.findall(year_pattern, stmt2))

            if years1 and years2 and years1 != years2 and _statements_related(
                stmt1, stmt2
            ):
                # Statements are about similar topics with conflicting years
                contradictions.append({
                    "fact1": stmt1,
                    "fact1_source": fact1.get("source"),
                    "fact2": stmt2,
                    "fact2_source": fact2.get("source"),
                    "type": "year_conflict",
                    "values": {"fact1": list(years1), "fact2": list(years2)}
                })
                continue

            # Check for number contradictions
            nums1 = re.findall(number_pattern, stmt1)
            nums2 = re.findall(number_pattern, stmt2)

            if nums1 and nums2 and _statements_related(stmt1, stmt2):
                # Compare first number found
                try:
                    n1 = float(re.sub(r"[^\d.]", "", nums1[0]))
                    n2 = float(re.sub(r"[^\d.]", "", nums2[0]))

                    # Significant difference (>20%)
                    if max(n1, n2) > 0 and abs(n1 - n2) / max(n1, n2) > 0.2:
                        contradictions.append({
                            "fact1": stmt1,
                            "fact1_source": fact1.get("source"),
                            "fact2": stmt2,
                            "fact2_source": fact2.get("source"),
                            "type": "number_conflict",
                            "values": {"fact1": n1, "fact2": n2}
                        })
                except (ValueError, IndexError):
                    pass

    logger.info("contradictions_detected", count=len(contradictions))
    return contradictions


def _statements_related(stmt1: str, stmt2: str) -> bool:
    """Check if two statements are about the same topic.

    Args:
        stmt1: First statement
        stmt2: Second statement

    Returns:
        True if statements appear related
    """
    # Common words to exclude
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
        "to", "for", "of", "and", "or", "but", "by", "from", "has", "have"
    }

    words1 = {
        w.lower()
        for w in re.findall(r"\b\w+\b", stmt1)
        if w.lower() not in stop_words and len(w) > 2
    }
    words2 = {
        w.lower()
        for w in re.findall(r"\b\w+\b", stmt2)
        if w.lower() not in stop_words and len(w) > 2
    }

    if not words1 or not words2:
        return False

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union > 0.3 if union > 0 else False


def calculate_fact_confidence(
    fact: dict[str, Any],
    contradictions: list[dict[str, Any]]
) -> float:
    """Calculate final confidence score for a fact.

    Factors:
    - Original extraction confidence
    - Number of supporting sources
    - Presence of contradictions

    Args:
        fact: Fact dictionary
        contradictions: List of detected contradictions

    Returns:
        Confidence score 0.0-1.0
    """
    base_confidence: float = float(fact.get("confidence", 0.5))

    # Boost for multiple sources
    supporting = fact.get("supporting_sources", [])
    source_boost = min(0.3, len(supporting) * 0.1)

    # Penalty for contradictions
    statement = fact.get("statement", "")
    contradiction_penalty = 0.0
    for c in contradictions:
        if statement in (c.get("fact1", ""), c.get("fact2", "")):
            contradiction_penalty = 0.3
            break

    final = base_confidence + source_boost - contradiction_penalty
    return max(0.1, min(1.0, final))


async def analyze_node(state: ResearchState) -> dict[str, Any]:
    """Analyze facts for cross-verification and confidence scoring.

    This node:
    1. Cross-references facts to find agreement
    2. Detects contradictions between facts
    3. Calculates final confidence scores
    4. Groups related facts together

    Args:
        state: Current research state

    Returns:
        dict: State updates with analysis results
    """
    logger.info("analyze_node_start")

    facts = state.get("facts_extracted", [])

    if not facts:
        logger.info("analyze_node_no_facts")
        return {
            "current_phase": "analyze",
            "fact_groups": [],
            "contradictions": [],
            "confidence_scores": {}
        }

    # Cross-reference facts
    fact_groups = await cross_reference_facts(facts)

    # Detect contradictions
    contradictions = await detect_contradictions(facts)

    # Calculate confidence scores
    confidence_scores = {}
    for i, fact in enumerate(facts):
        confidence_scores[f"fact_{i}"] = calculate_fact_confidence(
            fact, contradictions
        )

    # Update facts with group info
    for group in fact_groups:
        sources = group["unique_sources"]
        for fact in group["facts"]:
            fact["supporting_sources"] = sources
            fact["group_agreement"] = group["agreement_score"]

    logger.info(
        "analyze_node_complete",
        facts_analyzed=len(facts),
        groups_found=len(fact_groups),
        contradictions_found=len(contradictions)
    )

    return {
        "current_phase": "analyze",
        "fact_groups": fact_groups,
        "contradictions": contradictions,
        "confidence_scores": confidence_scores
    }
