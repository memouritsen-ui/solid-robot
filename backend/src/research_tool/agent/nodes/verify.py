"""Cross-verification node for fact checking and contradiction detection.

Implements LLM-based verification for:
- Fact extraction from content
- Cross-source verification
- Semantic contradiction detection
- Confidence scoring based on source agreement

Phase 4 Enhancement: Uses LLM for semantic understanding of contradictions
instead of simple regex-based pattern matching.
"""

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from research_tool.core.config import settings
from research_tool.core.logging import get_logger
from research_tool.models.entities import Fact
from research_tool.models.state import ResearchState
from research_tool.services.llm import get_llm_router

logger = get_logger(__name__)

# LLM prompt for contradiction detection
CONTRADICTION_DETECTION_PROMPT = """You are a fact-checker analyzing statements for contradictions.

Given these facts from different sources, identify:
1. Direct contradictions (same topic, conflicting claims)
2. Temporal inconsistencies (dates don't align)
3. Numerical discrepancies (numbers differ significantly)
4. Source reliability concerns

Facts to analyze:
{facts_json}

Respond in JSON format ONLY (no markdown, no explanation):
{{
  "contradictions": [
    {{
      "fact_indices": [0, 2],
      "type": "numerical|temporal|semantic|direct",
      "explanation": "Brief explanation of the contradiction",
      "resolution": "Which fact appears more reliable and why (or 'uncertain')"
    }}
  ],
  "low_confidence_facts": [1, 5],
  "high_confidence_facts": [0, 3, 4],
  "analysis_notes": "Brief overall assessment"
}}

Be conservative - only flag true contradictions, not minor variations or \
different perspectives on the same topic."""


async def detect_contradictions_llm(
    facts: list[Fact],
    model: str = "local-fast"
) -> dict[str, Any]:
    """Detect contradictions using LLM semantic analysis.

    Args:
        facts: List of facts to analyze
        model: LLM model to use for analysis

    Returns:
        dict with contradictions, low/high confidence facts, and notes
    """
    if len(facts) < 2:
        return {
            "contradictions": [],
            "low_confidence_facts": [],
            "high_confidence_facts": list(range(len(facts))),
            "analysis_notes": "Not enough facts to compare"
        }

    router = get_llm_router()
    if not router:
        logger.warning("llm_router_unavailable_for_verification")
        return {
            "contradictions": [],
            "low_confidence_facts": [],
            "high_confidence_facts": [],
            "analysis_notes": "LLM router not available"
        }

    # Prepare facts for LLM (limit to prevent token overflow)
    facts_for_analysis = facts[:20]  # Max 20 facts per batch
    facts_json = json.dumps([
        {
            "index": i,
            "statement": f.statement[:500],  # Truncate long statements
            "sources": f.sources[:3],  # Limit sources shown
            "confidence": f.confidence
        }
        for i, f in enumerate(facts_for_analysis)
    ], indent=2)

    prompt = CONTRADICTION_DETECTION_PROMPT.format(facts_json=facts_json)

    try:
        system_msg = "You are a precise fact-checker. Respond only in valid JSON."
        response = await router.complete(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            model=model,
            temperature=0.1,  # Low temperature for consistent analysis
            max_tokens=2000
        )

        # Parse JSON response
        # Handle potential markdown code blocks
        response_text = response
        if isinstance(response_text, str):
            response_text = response_text.strip()
            if response_text.startswith("```"):
                # Remove markdown code block
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

        result = json.loads(response_text)

        logger.info(
            "llm_contradiction_analysis_complete",
            contradictions_found=len(result.get("contradictions", [])),
            model=model
        )

        return result

    except json.JSONDecodeError as e:
        logger.warning(f"llm_response_parse_error: {e}")
        return {
            "contradictions": [],
            "low_confidence_facts": [],
            "high_confidence_facts": [],
            "analysis_notes": f"Failed to parse LLM response: {e}"
        }
    except Exception as e:
        logger.error(f"llm_contradiction_detection_failed: {e}")
        return {
            "contradictions": [],
            "low_confidence_facts": [],
            "high_confidence_facts": [],
            "analysis_notes": f"LLM analysis failed: {e}"
        }


@dataclass
class VerificationResult:
    """Result of verifying a single fact.

    Attributes:
        fact_id: Unique identifier for the fact
        original_statement: The fact statement being verified
        verified: Whether the fact passed verification
        confidence: Confidence score after verification (0.0-1.0)
        supporting_sources: Sources that support this fact
        contradicting_sources: Sources that contradict this fact
        contradiction_details: Details of any contradictions found
    """

    fact_id: str
    original_statement: str
    verified: bool
    confidence: float
    supporting_sources: list[str]
    contradicting_sources: list[str] = field(default_factory=list)
    contradiction_details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


def extract_facts_from_content(content: str, source_url: str) -> list[Fact]:
    """Extract factual statements from content.

    Uses simple heuristics to identify potential facts.
    Phase 5 enhancement: Will integrate with LLM for better extraction.

    Args:
        content: Text content to extract facts from
        source_url: URL of the source

    Returns:
        List of extracted Fact objects
    """
    if not content or not content.strip():
        return []

    facts: list[Fact] = []

    # Simple sentence-based extraction
    # Look for sentences with factual indicators
    sentences = re.split(r'[.!?]+', content)

    # Patterns that indicate factual statements
    factual_patterns = [
        r'\b(?:is|are|was|were|has|have|had)\b',  # State verbs
        r'\b(?:in|on|at)\s+\d{4}\b',  # Year references
        r'\b\d+(?:\.\d+)?%\b',  # Percentages
        r'\$\d+',  # Dollar amounts
        r'\b(?:million|billion|thousand)\b',  # Large numbers
        r'\b(?:founded|created|established|launched)\b',  # Creation verbs
    ]

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:  # Skip very short sentences
            continue

        # Check if sentence contains factual patterns
        is_factual = any(
            re.search(pattern, sentence, re.IGNORECASE)
            for pattern in factual_patterns
        )

        if is_factual:
            fact = Fact(
                statement=sentence,
                sources=[source_url],
                confidence=0.5,  # Initial confidence
                verified=False,
                extracted_at=datetime.now()
            )
            facts.append(fact)

    logger.debug(
        "facts_extracted",
        source=source_url,
        count=len(facts)
    )

    return facts


def detect_contradictions(
    facts: list[Fact]
) -> list[dict[str, Any]]:
    """Detect contradictions between facts.

    Compares facts to find conflicting information, particularly
    around dates, numbers, and key assertions.

    Args:
        facts: List of facts to compare

    Returns:
        List of contradiction pairs with details
    """
    contradictions: list[dict[str, Any]] = []

    # Patterns for extracting comparable values
    year_pattern = r'\b((19|20)\d{2})\b'  # Capture full year in group 1
    dollar_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d+)?)'

    for i, fact1 in enumerate(facts):
        for fact2 in facts[i + 1:]:
            # Skip if same source (can't contradict itself)
            if set(fact1.sources) == set(fact2.sources):
                continue

            # Check for year contradictions (extract full year from group 1)
            years1_matches = re.findall(year_pattern, fact1.statement)
            years2_matches = re.findall(year_pattern, fact2.statement)
            years1 = {m[0] for m in years1_matches}  # Full year is group 1
            years2 = {m[0] for m in years2_matches}

            if (
                years1 and years2 and years1 != years2
                and _statements_about_same_subject(
                    fact1.statement, fact2.statement
                )
            ):
                contradictions.append({
                    "fact1": fact1.statement,
                    "fact2": fact2.statement,
                    "reason": f"Conflicting years: {years1} vs {years2}",
                    "type": "year_conflict"
                })
                continue

            # Check for dollar amount contradictions
            dollars1 = re.findall(dollar_pattern, fact1.statement)
            dollars2 = re.findall(dollar_pattern, fact2.statement)

            if dollars1 and dollars2:
                d1 = _parse_number(dollars1[0])
                d2 = _parse_number(dollars2[0])
                # Significant difference (more than 20%)
                if (
                    d1 and d2
                    and abs(d1 - d2) / max(d1, d2) > 0.2
                    and _statements_about_same_subject(
                        fact1.statement, fact2.statement
                    )
                ):
                    contradictions.append({
                        "fact1": fact1.statement,
                        "fact2": fact2.statement,
                        "reason": f"Conflicting amounts: ${d1} vs ${d2}",
                        "type": "amount_conflict"
                    })

    logger.info(
        "contradictions_detected",
        count=len(contradictions)
    )

    return contradictions


def _statements_about_same_subject(stmt1: str, stmt2: str) -> bool:
    """Check if two statements are about the same subject.

    Simple heuristic based on word overlap.
    Phase 5 enhancement: Use NLP for better subject matching.

    Args:
        stmt1: First statement
        stmt2: Second statement

    Returns:
        True if statements appear to be about same subject
    """
    # Extract significant words (excluding common words)
    common_words = {
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
        "to", "for", "of", "and", "or", "but", "with", "by", "from"
    }

    words1 = {
        w.lower() for w in re.findall(r'\b\w+\b', stmt1)
        if w.lower() not in common_words and len(w) > 2
    }
    words2 = {
        w.lower() for w in re.findall(r'\b\w+\b', stmt2)
        if w.lower() not in common_words and len(w) > 2
    }

    if not words1 or not words2:
        return False

    # Calculate Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    similarity = intersection / union if union > 0 else 0

    # Threshold for considering statements related
    return similarity > 0.3


def _parse_number(num_str: str) -> float | None:
    """Parse a number string, handling commas."""
    try:
        return float(num_str.replace(",", ""))
    except ValueError:
        return None


def calculate_source_agreement(fact: Fact) -> float:
    """Calculate source agreement score for a fact.

    More sources supporting a fact = higher agreement score.

    Args:
        fact: Fact to calculate agreement for

    Returns:
        Agreement score (0.0-1.0)
    """
    num_sources = len(fact.sources)

    if num_sources == 0:
        return 0.0

    if num_sources == 1:
        return 0.3  # Single source = low agreement

    # Logarithmic scaling for multiple sources
    # 2 sources = 0.5, 3 sources = 0.65, 5 sources = 0.8, 10+ sources = ~0.95
    import math
    agreement = min(1.0, 0.3 + 0.35 * math.log2(num_sources))

    # Boost if fact is marked as verified
    if fact.verified:
        agreement = min(1.0, agreement + 0.1)

    return agreement


async def verify_node(state: ResearchState) -> dict[str, Any]:
    """Cross-verify facts and detect contradictions.

    LangGraph node that:
    1. Extracts facts from collected content
    2. Cross-references facts across sources
    3. Detects contradictions (LLM-based if available, regex fallback)
    4. Calculates confidence scores

    Phase 4 Enhancement: Uses LLM for semantic contradiction detection
    with automatic fallback to regex-based detection.

    Args:
        state: Current research state

    Returns:
        dict: State updates including verification results
    """
    logger.info("verify_node_start")

    # Get facts from state
    facts_data = state.get("facts_extracted", [])

    # Convert dict facts to Fact objects if needed
    facts: list[Fact] = []
    for fd in facts_data:
        if isinstance(fd, dict):
            facts.append(Fact(
                statement=fd.get("statement", ""),
                sources=fd.get("sources", []),
                confidence=fd.get("confidence", 0.5),
                verified=fd.get("verified", False),
                contradictions=fd.get("contradictions", []),
                extracted_at=fd.get("extracted_at", datetime.now())
            ))
        elif isinstance(fd, Fact):
            facts.append(fd)

    # Try LLM-based contradiction detection first
    llm_analysis: dict[str, Any] | None = None
    use_llm = settings.llm_enabled if hasattr(settings, 'llm_enabled') else True

    if use_llm and len(facts) >= 2:
        try:
            llm_analysis = await detect_contradictions_llm(facts, model="local-fast")
            logger.info("llm_verification_used")
        except Exception as e:
            logger.warning(f"llm_verification_fallback: {e}")
            llm_analysis = None

    # Fall back to regex-based detection if LLM unavailable or failed
    if llm_analysis is None or not llm_analysis.get("contradictions"):
        regex_contradictions = detect_contradictions(facts)
        # Convert to LLM format for unified processing
        llm_analysis = {
            "contradictions": [
                {
                    "fact_indices": [
                        next((i for i, f in enumerate(facts) if f.statement == c["fact1"]), -1),
                        next((i for i, f in enumerate(facts) if f.statement == c["fact2"]), -1)
                    ],
                    "type": c.get("type", "unknown"),
                    "explanation": c.get("reason", ""),
                    "resolution": "uncertain"
                }
                for c in regex_contradictions
            ],
            "low_confidence_facts": [],
            "high_confidence_facts": [],
            "analysis_notes": "Regex-based detection (LLM fallback)"
        }

    # Calculate verification results
    verification_results: list[dict[str, Any]] = []
    contradictions_output: list[dict[str, Any]] = []

    # Track which fact indices have contradictions
    contradicted_indices: set[int] = set()
    for c in llm_analysis.get("contradictions", []):
        indices = c.get("fact_indices", [])
        contradicted_indices.update(indices)
        # Build contradiction record for output
        if len(indices) >= 2 and all(0 <= idx < len(facts) for idx in indices):
            contradictions_output.append({
                "fact1": facts[indices[0]].statement,
                "fact2": facts[indices[1]].statement,
                "reason": c.get("explanation", "Unknown"),
                "type": c.get("type", "unknown"),
                "resolution": c.get("resolution", "uncertain")
            })

    # Get LLM confidence assessments
    low_confidence_indices = set(llm_analysis.get("low_confidence_facts", []))
    high_confidence_indices = set(llm_analysis.get("high_confidence_facts", []))

    for i, fact in enumerate(facts):
        # Calculate source agreement
        agreement = calculate_source_agreement(fact)

        # Adjust based on LLM analysis
        final_confidence = agreement

        # Reduce confidence for contradicted facts
        if i in contradicted_indices:
            final_confidence = max(0.1, final_confidence - 0.3)

        # Apply LLM confidence assessments
        if i in low_confidence_indices:
            final_confidence = max(0.1, final_confidence - 0.2)
        elif i in high_confidence_indices:
            final_confidence = min(1.0, final_confidence + 0.1)

        # Get contradiction details for this fact
        fact_contradiction_details = [
            c["explanation"] for c in llm_analysis.get("contradictions", [])
            if i in c.get("fact_indices", [])
        ]

        # Create verification result
        result = VerificationResult(
            fact_id=f"fact_{i:03d}",
            original_statement=fact.statement,
            verified=i not in contradicted_indices and agreement > 0.5,
            confidence=final_confidence,
            supporting_sources=fact.sources,
            contradicting_sources=[],
            contradiction_details=fact_contradiction_details
        )
        verification_results.append(result.to_dict())

    logger.info(
        "verify_node_complete",
        facts_verified=len(verification_results),
        contradictions_found=len(contradictions_output),
        analysis_method="llm" if "LLM" not in llm_analysis.get("analysis_notes", "") else "regex"
    )

    return {
        "current_phase": "verify",
        "verification_results": verification_results,
        "contradictions": contradictions_output,
        "llm_analysis_notes": llm_analysis.get("analysis_notes", "")
    }
