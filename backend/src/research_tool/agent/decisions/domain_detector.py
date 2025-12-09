"""Domain detection from META guide Section 7.2.

Implements two detection methods:
1. Keyword-based detection (fast, accurate for known domains)
2. LLM-based detection (fallback for novel/ambiguous queries)
"""

from dataclasses import asdict, dataclass
from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.domain import DomainConfiguration

logger = get_logger(__name__)


# Domain keyword mappings (from DomainConfiguration + expanded)
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "medical": [
        "clinical", "patient", "treatment", "diagnosis", "therapy",
        "medical", "disease", "drug", "pharmaceutical", "healthcare",
        "symptom", "hospital", "doctor", "medicine", "health",
        "disorder", "syndrome", "pathology", "oncology", "cardiology"
    ],
    "competitive_intelligence": [
        "company", "market", "competitor", "funding", "product",
        "revenue", "startup", "acquisition", "valuation", "business",
        "industry", "investment", "stock", "profit", "sales",
        "enterprise", "corporation", "shareholder"
    ],
    "academic": [
        "research", "study", "paper", "journal", "peer-reviewed",
        "publication", "citation", "methodology", "hypothesis",
        "thesis", "dissertation", "scholar", "academic", "university",
        "professor", "experiment", "analysis"
    ],
    "regulatory": [
        "regulation", "compliance", "FDA", "policy", "law",
        "requirement", "standard", "guideline", "legal", "legislation",
        "government", "rule", "mandate", "authority", "approval",
        "license", "permit", "audit"
    ],
}


@dataclass
class DetectedDomain:
    """Result of domain detection.

    Attributes:
        domain: Detected domain name (medical, academic, etc.)
        confidence: Confidence score (0.0 - 1.0)
        matched_keywords: Keywords that matched
        detection_method: How domain was detected (keyword, llm)
    """

    domain: str
    confidence: float
    matched_keywords: list[str]
    detection_method: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


def get_domain_keywords(domain: str) -> list[str]:
    """Get keywords for a specific domain.

    Args:
        domain: Domain name (medical, academic, etc.)

    Returns:
        list[str]: Keywords for the domain, empty if unknown
    """
    return DOMAIN_KEYWORDS.get(domain, [])


def detect_domain(query: str) -> DetectedDomain:
    """Detect research domain from query using keyword matching.

    Implements keyword-based domain detection:
    1. Match query against domain keywords (case-insensitive)
    2. Calculate confidence based on keyword match density
    3. Select domain with highest match score

    Args:
        query: Research query

    Returns:
        DetectedDomain: Detection result with domain, confidence, and matched keywords
    """
    query_lower = query.lower()
    query_words = set(query_lower.split())

    logger.info(
        "domain_detection_start",
        query_length=len(query),
        word_count=len(query_words)
    )

    # Score each domain
    domain_scores: dict[str, tuple[float, list[str]]] = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        matched = []
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Check if keyword is in query (either as word or substring)
            if keyword_lower in query_words or keyword_lower in query_lower:
                matched.append(keyword_lower)

        if matched:
            # Confidence based on number of matches relative to total keywords
            # More matches = higher confidence, capped at 0.95
            raw_confidence = len(matched) / len(keywords)
            # Boost confidence if multiple keywords match
            confidence = min(0.95, raw_confidence + (len(matched) - 1) * 0.1)
            domain_scores[domain] = (confidence, matched)

    # Select best domain
    if not domain_scores:
        logger.info(
            "domain_detection_no_match",
            result="general"
        )
        return DetectedDomain(
            domain="general",
            confidence=0.3,
            matched_keywords=[],
            detection_method="keyword"
        )

    # Sort by confidence (highest first)
    sorted_domains = sorted(
        domain_scores.items(),
        key=lambda x: (x[1][0], len(x[1][1])),  # Sort by confidence, then by match count
        reverse=True
    )

    best_domain, (confidence, matched_keywords) = sorted_domains[0]

    logger.info(
        "domain_detection_result",
        domain=best_domain,
        confidence=confidence,
        matched_count=len(matched_keywords)
    )

    return DetectedDomain(
        domain=best_domain,
        confidence=confidence,
        matched_keywords=matched_keywords,
        detection_method="keyword"
    )


async def detect_domain_with_llm(query: str) -> DetectedDomain:
    """Detect domain using LLM as fallback.

    Used when keyword detection fails or has low confidence.
    This is a placeholder for Phase 5 - will integrate with LLM router.

    Args:
        query: Research query

    Returns:
        DetectedDomain: Detection result from LLM analysis
    """
    logger.info(
        "domain_detection_llm_fallback",
        query_length=len(query)
    )

    # Phase 5: Will integrate with LLM router for actual detection
    # For now, return general domain with medium confidence
    # The LLM will analyze the query and return a domain

    # Simple heuristic fallback until LLM integration
    # Check for any technology/CS related terms
    tech_terms = [
        "neural", "network", "algorithm", "computer",
        "software", "AI", "machine learning"
    ]
    query_lower = query.lower()

    for term in tech_terms:
        if term.lower() in query_lower:
            return DetectedDomain(
                domain="academic",  # Technology falls under academic
                confidence=0.5,
                matched_keywords=[term],
                detection_method="llm"
            )

    return DetectedDomain(
        domain="general",
        confidence=0.4,
        matched_keywords=[],
        detection_method="llm"
    )


def get_domain_configuration(detected: DetectedDomain) -> DomainConfiguration:
    """Get DomainConfiguration for detected domain.

    Args:
        detected: Detection result

    Returns:
        DomainConfiguration: Configuration for the detected domain
    """
    config_map = {
        "medical": DomainConfiguration.for_medical,
        "competitive_intelligence": DomainConfiguration.for_competitive_intelligence,
        "academic": DomainConfiguration.for_academic,
        "regulatory": DomainConfiguration.for_regulatory,
    }

    factory = config_map.get(detected.domain)
    if factory:
        return factory()

    return DomainConfiguration.default()
