"""Tests for export providers.

Tasks #260-266: Test export functionality for all formats.
"""

import json

import pytest

from research_tool.services.export import ExportFormat, ExportResult, ResearchExportData
from research_tool.services.export.json_export import JSONExporter
from research_tool.services.export.markdown import MarkdownExporter


@pytest.fixture
def sample_research_data() -> ResearchExportData:
    """Create sample research data for testing."""
    return ResearchExportData(
        query="What are the effects of climate change on coral reefs?",
        domain="academic",
        summary=(
            "Climate change significantly impacts coral reefs through ocean warming, "
            "acidification, and increased storm intensity. Studies show widespread "
            "bleaching events and ecosystem degradation."
        ),
        facts=[
            {
                "statement": "Ocean temperatures have risen 0.5 degrees C since 1970",
                "confidence": 0.95,
                "source": "IPCC",
                "verified": True,
            },
            {
                "statement": "50% of coral cover lost in Great Barrier Reef",
                "confidence": 0.88,
                "source": "Nature",
                "verified": True,
            },
            {
                "statement": "Ocean pH has decreased by 0.1 units",
                "confidence": 0.92,
                "source": "Science",
                "verified": False,
            },
        ],
        sources=[
            {
                "title": "IPCC Climate Report 2023",
                "url": "https://ipcc.ch/report/2023",
                "type": "government",
                "reliability_score": 0.95,
            },
            {
                "title": "Nature: Coral Reef Decline",
                "url": "https://nature.com/articles/coral-decline",
                "type": "academic",
                "reliability_score": 0.90,
            },
        ],
        confidence_score=0.85,
        limitations=[
            "Study limited to Pacific region",
            "Data from 2020-2023 only",
            "Some sources behind paywall",
        ],
        metadata={"research_id": "test-123", "duration_seconds": 120},
    )


class TestResearchExportData:
    """Tests for ResearchExportData dataclass."""

    def test_create_research_export_data(
        self, sample_research_data: ResearchExportData
    ) -> None:
        """Test creating ResearchExportData instance."""
        assert sample_research_data.query == (
            "What are the effects of climate change on coral reefs?"
        )
        assert sample_research_data.domain == "academic"
        assert len(sample_research_data.facts) == 3
        assert len(sample_research_data.sources) == 2
        assert len(sample_research_data.limitations) == 3


class TestExportResult:
    """Tests for ExportResult dataclass."""

    def test_successful_export_result(self) -> None:
        """Test successful export result."""
        result = ExportResult(
            success=True,
            format=ExportFormat.MARKDOWN,
            content="# Test",
            filename="test.md",
            mime_type="text/markdown",
        )

        assert result.success is True
        assert result.format == ExportFormat.MARKDOWN
        assert result.content == "# Test"
        assert result.error is None

    def test_failed_export_result(self) -> None:
        """Test failed export result."""
        result = ExportResult(
            success=False,
            format=ExportFormat.PDF,
            content=None,
            filename="test.pdf",
            mime_type="application/pdf",
            error="Template not found",
        )

        assert result.success is False
        assert result.content is None
        assert result.error == "Template not found"

    def test_is_binary_property(self) -> None:
        """Test is_binary property for different formats."""
        text_result = ExportResult(
            success=True,
            format=ExportFormat.MARKDOWN,
            content="text",
            filename="test.md",
            mime_type="text/markdown",
        )
        binary_result = ExportResult(
            success=True,
            format=ExportFormat.PDF,
            content=b"binary",
            filename="test.pdf",
            mime_type="application/pdf",
        )

        assert text_result.is_binary is False
        assert binary_result.is_binary is True


class TestMarkdownExporter:
    """Tests for Markdown export (#260)."""

    @pytest.fixture
    def exporter(self) -> MarkdownExporter:
        """Create MarkdownExporter instance."""
        return MarkdownExporter()

    def test_format_property(self, exporter: MarkdownExporter) -> None:
        """Test format property returns MARKDOWN."""
        assert exporter.format == ExportFormat.MARKDOWN

    def test_mime_type_property(self, exporter: MarkdownExporter) -> None:
        """Test mime_type property."""
        assert exporter.mime_type == "text/markdown"

    def test_file_extension_property(self, exporter: MarkdownExporter) -> None:
        """Test file_extension property."""
        assert exporter.file_extension == "md"

    @pytest.mark.asyncio
    async def test_export_returns_valid_markdown(
        self, exporter: MarkdownExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test export produces valid Markdown content."""
        result = await exporter.export(sample_research_data)

        assert result.success is True
        assert result.format == ExportFormat.MARKDOWN
        assert isinstance(result.content, str)
        assert result.error is None

    @pytest.mark.asyncio
    async def test_markdown_contains_title(
        self, exporter: MarkdownExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test Markdown contains query as title."""
        result = await exporter.export(sample_research_data)

        assert "# Research Report" in result.content
        assert "climate change" in result.content.lower()

    @pytest.mark.asyncio
    async def test_markdown_contains_summary(
        self, exporter: MarkdownExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test Markdown contains executive summary."""
        result = await exporter.export(sample_research_data)

        assert "## Executive Summary" in result.content
        assert "coral reefs" in result.content.lower()

    @pytest.mark.asyncio
    async def test_markdown_contains_findings(
        self, exporter: MarkdownExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test Markdown contains key findings."""
        result = await exporter.export(sample_research_data)

        assert "## Key Findings" in result.content
        assert "Finding 1" in result.content
        assert "IPCC" in result.content

    @pytest.mark.asyncio
    async def test_markdown_contains_sources(
        self, exporter: MarkdownExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test Markdown contains sources section."""
        result = await exporter.export(sample_research_data)

        assert "## Sources" in result.content
        assert "IPCC Climate Report" in result.content

    @pytest.mark.asyncio
    async def test_markdown_contains_limitations(
        self, exporter: MarkdownExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test Markdown contains limitations section."""
        result = await exporter.export(sample_research_data)

        assert "## Limitations" in result.content
        assert "Pacific region" in result.content

    @pytest.mark.asyncio
    async def test_markdown_contains_disclaimer(
        self, exporter: MarkdownExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test Markdown contains disclaimer footer."""
        result = await exporter.export(sample_research_data)

        assert "generated automatically" in result.content.lower()
        assert "verify" in result.content.lower()

    def test_generate_filename(self, exporter: MarkdownExporter) -> None:
        """Test filename generation from query."""
        filename = exporter.generate_filename("Test query with spaces!")

        assert filename.endswith(".md")
        assert "Test_query_with_spaces" in filename
        assert "!" not in filename  # Special chars removed


class TestJSONExporter:
    """Tests for JSON export (#261)."""

    @pytest.fixture
    def exporter(self) -> JSONExporter:
        """Create JSONExporter instance."""
        return JSONExporter()

    def test_format_property(self, exporter: JSONExporter) -> None:
        """Test format property returns JSON."""
        assert exporter.format == ExportFormat.JSON

    def test_mime_type_property(self, exporter: JSONExporter) -> None:
        """Test mime_type property."""
        assert exporter.mime_type == "application/json"

    def test_file_extension_property(self, exporter: JSONExporter) -> None:
        """Test file_extension property."""
        assert exporter.file_extension == "json"

    @pytest.mark.asyncio
    async def test_export_returns_valid_json(
        self, exporter: JSONExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test export produces valid JSON content."""
        result = await exporter.export(sample_research_data)

        assert result.success is True
        assert result.format == ExportFormat.JSON
        assert isinstance(result.content, str)
        assert result.error is None

        # Should be valid JSON
        parsed = json.loads(result.content)
        assert isinstance(parsed, dict)

    @pytest.mark.asyncio
    async def test_json_contains_research_report(
        self, exporter: JSONExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test JSON contains research_report section."""
        result = await exporter.export(sample_research_data)
        parsed = json.loads(result.content)

        assert "research_report" in parsed
        assert parsed["research_report"]["query"] == sample_research_data.query
        assert parsed["research_report"]["domain"] == "academic"

    @pytest.mark.asyncio
    async def test_json_contains_facts(
        self, exporter: JSONExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test JSON contains facts array."""
        result = await exporter.export(sample_research_data)
        parsed = json.loads(result.content)

        assert "facts" in parsed
        assert len(parsed["facts"]) == 3
        assert parsed["facts"][0]["source"] == "IPCC"

    @pytest.mark.asyncio
    async def test_json_contains_sources(
        self, exporter: JSONExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test JSON contains sources array."""
        result = await exporter.export(sample_research_data)
        parsed = json.loads(result.content)

        assert "sources" in parsed
        assert len(parsed["sources"]) == 2

    @pytest.mark.asyncio
    async def test_json_contains_limitations(
        self, exporter: JSONExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test JSON contains limitations array."""
        result = await exporter.export(sample_research_data)
        parsed = json.loads(result.content)

        assert "limitations" in parsed
        assert len(parsed["limitations"]) == 3

    @pytest.mark.asyncio
    async def test_json_contains_metadata(
        self, exporter: JSONExporter, sample_research_data: ResearchExportData
    ) -> None:
        """Test JSON contains metadata."""
        result = await exporter.export(sample_research_data)
        parsed = json.loads(result.content)

        assert "metadata" in parsed
        assert parsed["metadata"]["research_id"] == "test-123"

    def test_generate_filename(self, exporter: JSONExporter) -> None:
        """Test filename generation from query."""
        filename = exporter.generate_filename("Test query")

        assert filename.endswith(".json")
        assert "Test_query" in filename


class TestLargeExport:
    """Test large export doesn't crash (#266)."""

    @pytest.fixture
    def large_research_data(self) -> ResearchExportData:
        """Create large research data with 1000 sources."""
        return ResearchExportData(
            query="Large scale research test",
            domain="academic",
            summary="Summary " * 100,  # Long summary
            facts=[
                {
                    "statement": f"Fact {i} statement " * 10,
                    "confidence": 0.85,
                    "source": f"Source {i}",
                    "verified": i % 2 == 0,
                }
                for i in range(100)  # 100 facts
            ],
            sources=[
                {
                    "title": f"Source Title {i}",
                    "url": f"https://example.com/source/{i}",
                    "type": "academic",
                    "reliability_score": 0.8,
                }
                for i in range(1000)  # 1000 sources
            ],
            confidence_score=0.75,
            limitations=[f"Limitation {i}" for i in range(20)],
            metadata={"large_test": True},
        )

    @pytest.mark.asyncio
    async def test_large_markdown_export(
        self, large_research_data: ResearchExportData
    ) -> None:
        """Test large Markdown export doesn't crash."""
        exporter = MarkdownExporter()
        result = await exporter.export(large_research_data)

        assert result.success is True
        assert len(result.content) > 10000  # Should be substantial

    @pytest.mark.asyncio
    async def test_large_json_export(
        self, large_research_data: ResearchExportData
    ) -> None:
        """Test large JSON export doesn't crash."""
        exporter = JSONExporter()
        result = await exporter.export(large_research_data)

        assert result.success is True
        parsed = json.loads(result.content)
        assert len(parsed["sources"]) == 1000
