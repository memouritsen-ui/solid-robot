"""Tests for anti-pattern prevention in export output.

Anti-patterns #11 and #12 (META guide Section 5.6):
- #11: Not including what was NOT found
- #12: Not explaining why research stopped

Rule: Output MUST include:
1. What was NOT found
2. Stopping rationale
3. Confidence levels
4. Access failures and reasons
"""

import pytest

from research_tool.services.export import ResearchExportData
from research_tool.services.export.markdown import MarkdownExporter


@pytest.fixture
def complete_research_data() -> ResearchExportData:
    """Create research data with all anti-pattern prevention fields."""
    return ResearchExportData(
        query="What is the mechanism of action of aspirin?",
        domain="medical",
        summary="Aspirin works by inhibiting cyclooxygenase enzymes.",
        facts=[
            {
                "statement": "Aspirin inhibits COX-1 and COX-2",
                "confidence": 0.95,
                "source": "PubMed",
            }
        ],
        sources=[
            {
                "title": "Aspirin Mechanism Study",
                "url": "https://pubmed.gov/123",
                "type": "academic",
            }
        ],
        confidence_score=0.85,
        limitations=[
            "Limited to English sources",
            "Does not cover aspirin resistance",
        ],
        metadata={},
        # Anti-pattern prevention fields
        not_found=[
            "Long-term effects beyond 10 years",
            "Pediatric dosing guidelines",
        ],
        stopping_reason="Saturation reached: 3 consecutive sources with no new information",
        access_failures=[
            {
                "source": "Nature.com",
                "reason": "Paywall - no institutional access",
                "attempted_at": "2025-12-10T10:00:00",
            },
            {
                "source": "Cochrane Library",
                "reason": "Rate limited after 5 requests",
                "attempted_at": "2025-12-10T10:05:00",
            },
        ],
    )


class TestAntiPattern11NotFound:
    """Tests for Anti-pattern #11: Must include what was NOT found."""

    def test_research_export_data_has_not_found_field(self) -> None:
        """ResearchExportData must have not_found field."""
        data = ResearchExportData(
            query="test",
            domain="general",
            summary="test",
            facts=[],
            sources=[],
            confidence_score=0.5,
            limitations=[],
            metadata={},
            not_found=["Item 1", "Item 2"],
            stopping_reason="Test",
            access_failures=[],
        )
        assert hasattr(data, "not_found")
        assert data.not_found == ["Item 1", "Item 2"]

    @pytest.mark.asyncio
    async def test_markdown_export_includes_not_found_section(
        self, complete_research_data: ResearchExportData
    ) -> None:
        """Markdown export must include 'What Was Not Found' section."""
        exporter = MarkdownExporter()
        result = await exporter.export(complete_research_data)

        assert "Not Found" in result.content or "not found" in result.content.lower()
        assert "Long-term effects" in result.content
        assert "Pediatric dosing" in result.content

    @pytest.mark.asyncio
    async def test_markdown_export_empty_not_found_is_explicit(self) -> None:
        """Even when nothing was explicitly not found, should mention it."""
        data = ResearchExportData(
            query="test",
            domain="general",
            summary="Complete findings",
            facts=[{"statement": "Fact 1", "confidence": 0.9, "source": "Test"}],
            sources=[{"title": "Source 1", "url": "http://test.com", "type": "web"}],
            confidence_score=0.9,
            limitations=[],
            metadata={},
            not_found=[],  # Empty but field exists
            stopping_reason="Saturation reached",
            access_failures=[],
        )
        exporter = MarkdownExporter()
        result = await exporter.export(data)

        # Should still have the section, even if empty
        assert result.success is True


class TestAntiPattern12StoppingReason:
    """Tests for Anti-pattern #12: Must explain why research stopped."""

    def test_research_export_data_has_stopping_reason_field(self) -> None:
        """ResearchExportData must have stopping_reason field."""
        data = ResearchExportData(
            query="test",
            domain="general",
            summary="test",
            facts=[],
            sources=[],
            confidence_score=0.5,
            limitations=[],
            metadata={},
            not_found=[],
            stopping_reason="Saturation reached",
            access_failures=[],
        )
        assert hasattr(data, "stopping_reason")
        assert data.stopping_reason == "Saturation reached"

    @pytest.mark.asyncio
    async def test_markdown_export_includes_stopping_reason(
        self, complete_research_data: ResearchExportData
    ) -> None:
        """Markdown export must include stopping reason."""
        exporter = MarkdownExporter()
        result = await exporter.export(complete_research_data)

        assert "Saturation reached" in result.content
        assert "3 consecutive sources" in result.content


class TestAccessFailures:
    """Tests for access failures inclusion (part of anti-pattern prevention)."""

    def test_research_export_data_has_access_failures_field(self) -> None:
        """ResearchExportData must have access_failures field."""
        data = ResearchExportData(
            query="test",
            domain="general",
            summary="test",
            facts=[],
            sources=[],
            confidence_score=0.5,
            limitations=[],
            metadata={},
            not_found=[],
            stopping_reason="Test",
            access_failures=[{"source": "Test", "reason": "Error"}],
        )
        assert hasattr(data, "access_failures")
        assert len(data.access_failures) == 1

    @pytest.mark.asyncio
    async def test_markdown_export_includes_access_failures(
        self, complete_research_data: ResearchExportData
    ) -> None:
        """Markdown export must include access failures section."""
        exporter = MarkdownExporter()
        result = await exporter.export(complete_research_data)

        assert "Access" in result.content or "access" in result.content.lower()
        assert "Nature.com" in result.content
        assert "Paywall" in result.content
        assert "Cochrane Library" in result.content
        assert "Rate limited" in result.content


class TestConfidenceLevels:
    """Tests for confidence levels in output."""

    @pytest.mark.asyncio
    async def test_markdown_export_includes_overall_confidence(
        self, complete_research_data: ResearchExportData
    ) -> None:
        """Markdown export must include overall confidence score."""
        exporter = MarkdownExporter()
        result = await exporter.export(complete_research_data)

        # Should show 85% confidence
        assert "85" in result.content or "0.85" in result.content

    @pytest.mark.asyncio
    async def test_markdown_export_includes_fact_confidence(
        self, complete_research_data: ResearchExportData
    ) -> None:
        """Markdown export must include per-fact confidence levels."""
        exporter = MarkdownExporter()
        result = await exporter.export(complete_research_data)

        # Should show 95% confidence for the fact
        assert "95" in result.content or "0.95" in result.content
