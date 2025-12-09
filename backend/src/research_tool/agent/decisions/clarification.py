"""Clarification decision tree from META guide Section 7.3."""

from research_tool.core.logging import get_logger

logger = get_logger(__name__)


def should_ask_for_clarification(
    query: str,
    domain: str | None,
    scope_clear: bool,
    has_ambiguous_terms: bool,
    clarification_count: int = 0
) -> tuple[bool, str | None]:
    """Determine if clarification is needed before starting research.

    Implements META guide Section 7.3 Clarification Decision Tree:
    - Maximum 2 clarifying exchanges before starting
    - Only ask when genuinely needed
    - Prefer reasonable defaults over asking

    Args:
        query: User's research query
        domain: Detected domain (None if unknown)
        scope_clear: Whether research scope is clear
        has_ambiguous_terms: Whether query has ambiguous terms
        clarification_count: Number of clarifications already asked

    Returns:
        tuple[bool, str | None]: (should_ask, question_to_ask)
    """
    logger.info(
        "clarification_check",
        domain=domain,
        scope_clear=scope_clear,
        has_ambiguous=has_ambiguous_terms,
        clarification_count=clarification_count
    )

    # RULE: Maximum 2 clarifying exchanges before starting
    if clarification_count >= 2:
        logger.info(
            "clarification_limit_reached",
            message="Starting with best interpretation"
        )
        return False, None

    # Decision tree: Can I determine the research domain?
    if domain is None:
        # NO - domain unknown
        if _has_reasonable_default_interpretation(query):
            # YES - pick most likely, note assumption
            logger.info(
                "clarification_domain_assumed",
                assumption="Using general domain"
            )
            return False, None
        else:
            # NO - ask for domain
            return True, "What field or industry is this related to?"

    # Decision tree: Can I determine the scope?
    if not scope_clear:
        if _is_broad_scope_acceptable(query):
            # YES - use broad scope
            logger.info(
                "clarification_broad_scope",
                message="Using broad scope, will narrow based on results"
            )
            return False, None
        else:
            # NO - ask for scope
            return True, _generate_scope_question(query, domain)

    # Decision tree: Are there ambiguous terms?
    if has_ambiguous_terms:
        if _can_resolve_from_context(query):
            # YES - resolve from context
            logger.info(
                "clarification_context_resolved",
                message="Resolved ambiguity from context"
            )
            return False, None
        else:
            # Will wrong interpretation waste significant effort?
            if _wrong_interpretation_costly(query, domain):
                # YES - ask for disambiguation
                return True, _generate_disambiguation_question(query)
            else:
                # NO - pick most common interpretation
                logger.info(
                    "clarification_common_interpretation",
                    message="Using most common interpretation"
                )
                return False, None

    # Do I have enough to start?
    logger.info(
        "clarification_sufficient",
        message="Sufficient information to begin research"
    )
    return False, None


def _has_reasonable_default_interpretation(query: str) -> bool:
    """Check if query has a reasonable default domain interpretation.

    Args:
        query: Research query

    Returns:
        bool: True if default interpretation exists
    """
    # Simple heuristic: if query is detailed (>10 words), likely has context
    word_count = len(query.split())
    return word_count >= 10


def _is_broad_scope_acceptable(query: str) -> bool:
    """Check if broad scope won't overwhelm the research.

    Args:
        query: Research query

    Returns:
        bool: True if broad scope is acceptable
    """
    # Simple heuristic: short queries benefit from broad scope
    # Long, specific queries likely need narrower scope
    word_count = len(query.split())
    return word_count <= 15


def _can_resolve_from_context(query: str) -> bool:
    """Check if ambiguity can be resolved from query context.

    Args:
        query: Research query

    Returns:
        bool: True if context provides resolution
    """
    # Simple heuristic: longer queries have more context
    # Phase 5 will implement actual NLP context analysis
    word_count = len(query.split())
    return word_count >= 8


def _wrong_interpretation_costly(query: str, domain: str | None) -> bool:
    """Check if wrong interpretation would waste significant effort.

    Args:
        query: Research query
        domain: Detected domain

    Returns:
        bool: True if misinterpretation is costly
    """
    # Medical and regulatory domains have high cost of wrong interpretation
    high_cost_domains = {"medical", "regulatory", "legal", "pharmaceutical"}

    # Return True if domain is high-cost
    return bool(domain and domain.lower() in high_cost_domains)


def _generate_scope_question(query: str, domain: str | None) -> str:
    """Generate a scope clarification question.

    Args:
        query: Research query
        domain: Detected domain

    Returns:
        str: Question to ask user
    """
    # Generic scope question
    if domain:
        return (
            f"Should I focus on recent developments or "
            f"comprehensive historical {domain} research?"
        )
    return "Should I focus on recent information or comprehensive historical coverage?"


def _generate_disambiguation_question(query: str) -> str:
    """Generate a disambiguation question for ambiguous terms.

    Args:
        query: Research query

    Returns:
        str: Question to ask user
    """
    # Simple disambiguation - Phase 5 will detect specific ambiguous terms
    return "Could you clarify what you mean by this? (I want to ensure I understand correctly)"


def extract_ambiguous_terms(query: str) -> list[str]:
    """Extract potentially ambiguous terms from query.

    This is a simple implementation. Phase 5 will use NLP for better detection.

    Args:
        query: Research query

    Returns:
        list[str]: List of potentially ambiguous terms
    """
    # Simple heuristic: very short queries or vague terms
    ambiguous_indicators = ["it", "that", "this", "they", "them", "thing"]

    query_lower = query.lower()
    words = query_lower.split()

    ambiguous = []
    for indicator in ambiguous_indicators:
        if indicator in words:
            ambiguous.append(indicator)

    return ambiguous
