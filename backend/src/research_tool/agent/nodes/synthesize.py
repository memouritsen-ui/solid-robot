"""Synthesis node - generate final research report using LLM."""

from datetime import datetime
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


SUMMARY_PROMPT = """You are a research analyst writing an executive summary.

Research Question: {query}
Domain: {domain}

Key Findings:
{findings}

Write a concise executive summary (2-3 paragraphs) that:
1. Directly answers the research question
2. Highlights the most important findings
3. Notes the confidence level based on source agreement
4. Is written in a professional, objective tone

Write ONLY the summary, no headers or labels."""


async def generate_executive_summary(
    query: str,
    facts: list[dict[str, Any]],
    domain: str
) -> str:
    """Generate executive summary using LLM.

    Args:
        query: Original research question
        facts: Extracted and verified facts
        domain: Research domain

    Returns:
        Executive summary text
    """
    if not facts:
        return (
            "No facts were extracted from the sources. "
            "The research query may need refinement or additional sources."
        )

    # Format findings for prompt
    findings_lines: list[str] = []
    for f in facts[:10]:  # Top 10 facts
        conf = f.get("confidence", 0.5)
        sources = f.get("supporting_sources", [f.get("source", "unknown")])
        source_count = len(sources) if isinstance(sources, list) else 1
        findings_lines.append(
            f"- {f['statement']} (confidence: {conf:.0%}, sources: {source_count})"
        )
    findings_text = "\n".join(findings_lines)

    router = get_llm_router()

    prompt = SUMMARY_PROMPT.format(
        query=query,
        domain=domain,
        findings=findings_text
    )

    try:
        response = await router.complete(
            messages=[{"role": "user", "content": prompt}],
            model="cloud-best",  # Use best model for synthesis
            temperature=0.3,
            max_tokens=500,
            stream=False
        )
        assert isinstance(response, str), "Expected string response"
        return response.strip()

    except Exception as e:
        logger.error("summary_generation_failed", error=str(e))
        # Fallback to simple summary
        first_fact = facts[0]["statement"] if facts else "None"
        return (
            f"Research on '{query}' found {len(facts)} key findings. "
            f"The highest confidence finding: {first_fact}."
        )


def generate_limitations(
    sources_queried: list[str],
    contradictions: list[dict[str, Any]],
    domain: str
) -> list[str]:
    """Generate list of research limitations.

    Args:
        sources_queried: List of sources that were searched
        contradictions: Detected contradictions
        domain: Research domain

    Returns:
        List of limitation statements
    """
    limitations: list[str] = []

    # Source coverage
    all_sources = {"pubmed", "arxiv", "semantic_scholar", "tavily", "brave"}
    missing = all_sources - set(sources_queried)
    if missing:
        limitations.append(
            f"Not all sources were queried. Missing: {', '.join(missing)}"
        )

    # Contradictions
    if contradictions:
        limitations.append(
            f"Found {len(contradictions)} contradicting claims between sources. "
            "Manual verification recommended."
        )

    # Domain-specific
    if domain == "medical":
        limitations.append(
            "Medical information should be verified by healthcare professionals. "
            "This research is not a substitute for medical advice."
        )
    elif domain == "academic":
        limitations.append(
            "Academic claims should be verified against primary sources. "
            "Citation analysis was limited to available metadata."
        )

    # General
    limitations.append(
        "This research represents a snapshot in time. "
        "Information may have changed since sources were published."
    )

    return limitations


async def synthesize_node(state: ResearchState) -> dict[str, Any]:
    """Synthesize research findings into final report.

    This node:
    1. Generates executive summary using LLM
    2. Organizes findings by confidence
    3. Documents methodology and limitations
    4. Creates structured report

    Anti-pattern prevention:
    - Include what was NOT found (Anti-Pattern #11)
    - Explain stopping rationale (Anti-Pattern #12)

    Args:
        state: Current research state

    Returns:
        dict: State updates with final report
    """
    logger.info("synthesize_node_start")

    # Extract values with proper type handling
    query = str(state.get("refined_query") or state.get("original_query") or "")
    domain = str(state.get("domain") or "general")
    stop_reason = str(state.get("stop_reason") or "Unknown")

    # Lists with type guards
    facts_raw = state.get("facts_extracted")
    facts: list[dict[str, Any]] = facts_raw if isinstance(facts_raw, list) else []

    sources_raw = state.get("sources_queried")
    sources_queried: list[str] = sources_raw if isinstance(sources_raw, list) else []

    entities_raw = state.get("entities_found")
    entities: list[dict[str, Any]] = entities_raw if isinstance(entities_raw, list) else []

    contradictions_raw = state.get("contradictions")
    contradictions: list[dict[str, Any]] = (
        contradictions_raw if isinstance(contradictions_raw, list) else []
    )

    saturation_raw = state.get("saturation_metrics")
    saturation: dict[str, Any] = (
        saturation_raw if isinstance(saturation_raw, dict) else {}
    )

    # Generate executive summary
    summary = await generate_executive_summary(query, facts, domain)

    # Sort facts by confidence
    sorted_facts = sorted(
        facts,
        key=lambda f: float(f.get("confidence", 0)),
        reverse=True
    )

    # Generate limitations
    limitations = generate_limitations(sources_queried, contradictions, domain)

    # Calculate overall confidence
    overall_confidence: float = 0.0
    if facts:
        total = sum(float(f.get("confidence", 0.5)) for f in facts)
        overall_confidence = total / len(facts)

    # Build findings list
    findings_list: list[dict[str, Any]] = [
        {
            "statement": f["statement"],
            "confidence": f.get("confidence", 0.5),
            "source": f.get("source", "Unknown"),
            "supporting_sources": f.get("supporting_sources", [])
        }
        for f in sorted_facts[:20]
    ]

    # Build sources list
    sources_list: list[dict[str, Any]] = [
        {
            "url": e.get("url", ""),
            "title": e.get("title", "Unknown"),
            "type": e.get("source_name", "web")
        }
        for e in entities[:30]
    ]

    # Build report
    report: dict[str, Any] = {
        "query": query,
        "domain": domain,
        "generated_at": datetime.now().isoformat(),

        # Summary
        "summary": summary,

        # Findings (sorted by confidence)
        "findings": findings_list,

        # Sources
        "sources": sources_list,

        # Methodology
        "methodology": {
            "sources_queried": sources_queried,
            "entities_found": len(entities),
            "facts_extracted": len(facts),
            "saturation_metrics": saturation,
            "stop_reason": stop_reason
        },

        # Limitations and gaps
        "limitations": limitations,
        "contradictions_found": len(contradictions),

        # Confidence metrics
        "overall_confidence": overall_confidence
    }

    logger.info(
        "synthesize_node_complete",
        findings_count=len(findings_list),
        sources_count=len(sources_list),
        overall_confidence=overall_confidence
    )

    return {
        "final_report": report,
        "current_phase": "synthesize"
    }
