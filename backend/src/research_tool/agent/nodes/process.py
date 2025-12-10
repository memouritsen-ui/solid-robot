"""Processing node - extract entities and facts from collected data using LLM."""

import hashlib
import json
from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.state import ResearchState
from research_tool.services.llm.router import LLMRouter

logger = get_logger(__name__)

# Initialize LLM router
_llm_router: LLMRouter | None = None


def get_llm_router() -> LLMRouter:
    """Get or create the LLM router instance."""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router


FACT_EXTRACTION_PROMPT = """You are a fact extraction assistant. \
Extract factual statements from the provided content.

Rules:
1. Extract ONLY factual claims (not opinions or speculation)
2. Each fact should be a standalone statement
3. Include numerical data when present (percentages, dates, amounts)
4. Prioritize facts relevant to the query context
5. Rate confidence 0.0-1.0 based on how explicitly stated the fact is

Query context: {query_context}

Content to analyze:
{content}

Return JSON array of facts:
[
  {{"statement": "Factual statement here", "confidence": 0.8}},
  ...
]

Return ONLY the JSON array, no other text."""


async def extract_facts_with_llm(
    content: str,
    source_url: str,
    query_context: str
) -> list[dict[str, Any]]:
    """Extract facts from content using LLM.

    Args:
        content: Text content to extract facts from
        source_url: URL of the source for attribution
        query_context: Research query for relevance filtering

    Returns:
        List of fact dictionaries with statement, source, confidence
    """
    if not content or not content.strip():
        return []

    # Truncate content if too long (keep under 8000 chars for context)
    max_content_length = 8000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "..."

    router = get_llm_router()

    prompt = FACT_EXTRACTION_PROMPT.format(
        query_context=query_context,
        content=content
    )

    try:
        response = await router.complete(
            messages=[{"role": "user", "content": prompt}],
            model="local-fast",  # Use fast model for extraction
            temperature=0.1,  # Low temperature for factual extraction
            max_tokens=2000,
            stream=False  # Ensure we get string, not AsyncIterator
        )

        # Parse JSON response - response is str when stream=False
        assert isinstance(response, str), "Expected string response"
        response_text = response.strip()

        # Handle markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        facts_data = json.loads(response_text)

        # Normalize and add source
        facts = []
        for item in facts_data:
            if isinstance(item, dict) and "statement" in item:
                facts.append({
                    "statement": item["statement"],
                    "source": source_url,
                    "confidence": float(item.get("confidence", 0.5)),
                    "extracted_by": "llm"
                })

        logger.info(
            "facts_extracted_llm",
            source=source_url,
            count=len(facts)
        )

        return facts

    except json.JSONDecodeError as e:
        logger.warning(
            "fact_extraction_json_error",
            source=source_url,
            error=str(e)
        )
        return []
    except Exception as e:
        logger.error(
            "fact_extraction_failed",
            source=source_url,
            error=str(e)
        )
        return []


def deduplicate_facts(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate facts based on statement similarity.

    Args:
        facts: List of fact dictionaries

    Returns:
        Deduplicated list of facts
    """
    seen_hashes: set[str] = set()
    unique_facts = []

    for fact in facts:
        # Create hash of normalized statement
        statement = fact.get("statement", "").lower().strip()
        fact_hash = hashlib.md5(statement.encode()).hexdigest()  # noqa: S324

        if fact_hash not in seen_hashes:
            seen_hashes.add(fact_hash)
            unique_facts.append(fact)

    return unique_facts


async def process_node(state: ResearchState) -> dict[str, Any]:
    """Process collected data to extract entities and facts using LLM.

    This node:
    1. Iterates through collected entities
    2. Uses LLM to extract factual statements from full content
    3. Deduplicates extracted facts
    4. Returns enriched state with facts

    Args:
        state: Current research state

    Returns:
        dict: State updates with extracted facts
    """
    logger.info("process_node_start")

    entities = state.get("entities_found", [])
    query = state.get("refined_query", state.get("original_query", ""))

    all_facts: list[dict[str, Any]] = []

    for entity in entities:
        # Prefer full_content, fall back to snippet
        content = entity.get("full_content") or entity.get("snippet", "")

        if not content:
            continue

        source_url = entity.get("url", "unknown")

        # Extract facts using LLM
        facts = await extract_facts_with_llm(
            content=content,
            source_url=source_url,
            query_context=query
        )

        all_facts.extend(facts)

    # Deduplicate
    unique_facts = deduplicate_facts(all_facts)

    logger.info(
        "process_node_complete",
        entities_processed=len(entities),
        facts_extracted=len(unique_facts),
        duplicates_removed=len(all_facts) - len(unique_facts)
    )

    return {
        "facts_extracted": unique_facts,
        "current_phase": "process"
    }
