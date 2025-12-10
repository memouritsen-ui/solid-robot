"""Tests for template loader and rendering."""

import pytest

from research_tool.services.export import ResearchExportData
from research_tool.services.export.template_loader import (
    TemplateLoader,
    get_template_loader,
)


@pytest.fixture
def sample_data() -> ResearchExportData:
    """Create sample research data for testing."""
    return ResearchExportData(
        query="What are the effects of caffeine?",
        domain="medical",
        summary="Caffeine is a stimulant that affects the central nervous system.",
        facts=[
            {
                "statement": "Caffeine blocks adenosine receptors",
                "confidence": 0.95,
                "source": "PubMed Study 123",
            },
            {
                "content": "Half-life is 5-6 hours",
                "confidence": 0.88,
                "source": "FDA Report",
            },
        ],
        sources=[
            {
                "title": "Caffeine Mechanisms Study",
                "url": "https://pubmed.ncbi.nlm.nih.gov/123",
                "type": "academic",
            },
            {
                "title": "FDA Caffeine Guidelines",
                "url": "https://fda.gov/caffeine",
                "type": "regulatory",
            },
        ],
        confidence_score=0.91,
        limitations=[
            "Limited to English-language sources",
            "Does not cover long-term effects",
        ],
        metadata={"session_id": "test-123"},
    )


@pytest.fixture
def template_loader() -> TemplateLoader:
    """Create template loader with default templates."""
    return TemplateLoader()


class TestTemplateLoader:
    """Tests for TemplateLoader class."""

    def test_default_template_dir_exists(self, template_loader: TemplateLoader) -> None:
        """Default template directory should exist."""
        assert template_loader.template_dir.exists()
        assert template_loader.template_dir.is_dir()

    def test_markdown_template_exists(self, template_loader: TemplateLoader) -> None:
        """Markdown template should exist."""
        md_template = template_loader.template_dir / "report.md.j2"
        assert md_template.exists(), f"Missing template: {md_template}"

    def test_html_template_exists(self, template_loader: TemplateLoader) -> None:
        """HTML template should exist."""
        html_template = template_loader.template_dir / "report.html.j2"
        assert html_template.exists(), f"Missing template: {html_template}"

    def test_get_template_name_default(self, template_loader: TemplateLoader) -> None:
        """Should return default template when no domain-specific exists."""
        name = template_loader.get_template_name("md")
        assert name == "report.md.j2"

    def test_get_template_name_with_domain_fallback(
        self, template_loader: TemplateLoader
    ) -> None:
        """Should fall back to default when domain template doesn't exist."""
        name = template_loader.get_template_name("md", domain="nonexistent")
        assert name == "report.md.j2"


class TestMarkdownRendering:
    """Tests for Markdown template rendering."""

    def test_render_markdown_contains_query(
        self, template_loader: TemplateLoader, sample_data: ResearchExportData
    ) -> None:
        """Rendered markdown should contain the query."""
        result = template_loader.render_markdown(sample_data)
        assert "What are the effects of caffeine?" in result

    def test_render_markdown_contains_summary(
        self, template_loader: TemplateLoader, sample_data: ResearchExportData
    ) -> None:
        """Rendered markdown should contain the summary."""
        result = template_loader.render_markdown(sample_data)
        assert "Caffeine is a stimulant" in result

    def test_render_markdown_contains_facts(
        self, template_loader: TemplateLoader, sample_data: ResearchExportData
    ) -> None:
        """Rendered markdown should contain facts."""
        result = template_loader.render_markdown(sample_data)
        assert "Caffeine blocks adenosine receptors" in result
        assert "Half-life is 5-6 hours" in result

    def test_render_markdown_contains_confidence(
        self, template_loader: TemplateLoader, sample_data: ResearchExportData
    ) -> None:
        """Rendered markdown should show confidence scores."""
        result = template_loader.render_markdown(sample_data)
        assert "91" in result  # Overall confidence 91%

    def test_render_markdown_contains_sources(
        self, template_loader: TemplateLoader, sample_data: ResearchExportData
    ) -> None:
        """Rendered markdown should list sources."""
        result = template_loader.render_markdown(sample_data)
        assert "Caffeine Mechanisms Study" in result
        assert "pubmed.ncbi.nlm.nih.gov" in result

    def test_render_markdown_contains_limitations(
        self, template_loader: TemplateLoader, sample_data: ResearchExportData
    ) -> None:
        """Rendered markdown should include limitations."""
        result = template_loader.render_markdown(sample_data)
        assert "Limited to English-language sources" in result
        assert "long-term effects" in result

    def test_render_markdown_has_structure(
        self, template_loader: TemplateLoader, sample_data: ResearchExportData
    ) -> None:
        """Rendered markdown should have proper structure."""
        result = template_loader.render_markdown(sample_data)
        assert "# Research Report:" in result
        assert "## Executive Summary" in result
        assert "## Key Findings" in result
        assert "## Sources" in result
        assert "## Limitations" in result


class TestHtmlRendering:
    """Tests for HTML template rendering."""

    def test_render_html_is_valid_html(
        self, template_loader: TemplateLoader, sample_data: ResearchExportData
    ) -> None:
        """Rendered HTML should be valid HTML document."""
        result = template_loader.render_html(sample_data)
        assert "<!DOCTYPE html>" in result
        assert "<html>" in result
        assert "</html>" in result
        assert "<head>" in result
        assert "<body>" in result

    def test_render_html_contains_query(
        self, template_loader: TemplateLoader, sample_data: ResearchExportData
    ) -> None:
        """Rendered HTML should contain the query."""
        result = template_loader.render_html(sample_data)
        assert "What are the effects of caffeine?" in result

    def test_render_html_escapes_special_chars(
        self, template_loader: TemplateLoader
    ) -> None:
        """HTML should escape special characters to prevent XSS."""
        data = ResearchExportData(
            query="Test <script>alert('xss')</script>",
            domain="general",
            summary="Summary with <b>html</b> tags",
            facts=[],
            sources=[],
            confidence_score=0.5,
            limitations=[],
            metadata={},
        )
        result = template_loader.render_html(data)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_render_html_contains_css(
        self, template_loader: TemplateLoader, sample_data: ResearchExportData
    ) -> None:
        """Rendered HTML should include CSS styling."""
        result = template_loader.render_html(sample_data)
        assert "<style>" in result
        assert "font-family" in result

    def test_render_html_contains_metadata(
        self, template_loader: TemplateLoader, sample_data: ResearchExportData
    ) -> None:
        """Rendered HTML should show metadata section."""
        result = template_loader.render_html(sample_data)
        assert "medical" in result  # domain
        assert "91" in result  # confidence


class TestEmptyData:
    """Tests for handling empty data."""

    def test_render_markdown_empty_facts(
        self, template_loader: TemplateLoader
    ) -> None:
        """Should handle empty facts list."""
        data = ResearchExportData(
            query="Test query",
            domain="general",
            summary="Test summary",
            facts=[],
            sources=[],
            confidence_score=0.5,
            limitations=[],
            metadata={},
        )
        result = template_loader.render_markdown(data)
        assert "Test query" in result
        assert "Test summary" in result
        # Should not have Key Findings section when empty
        # (depends on template implementation)

    def test_render_html_empty_sources(
        self, template_loader: TemplateLoader
    ) -> None:
        """Should handle empty sources list."""
        data = ResearchExportData(
            query="Test query",
            domain="general",
            summary="Test summary",
            facts=[],
            sources=[],
            confidence_score=0.5,
            limitations=[],
            metadata={},
        )
        result = template_loader.render_html(data)
        assert "<!DOCTYPE html>" in result


class TestGlobalLoader:
    """Tests for global template loader instance."""

    def test_get_template_loader_returns_instance(self) -> None:
        """Should return a TemplateLoader instance."""
        loader = get_template_loader()
        assert isinstance(loader, TemplateLoader)

    def test_get_template_loader_singleton(self) -> None:
        """Should return same instance on multiple calls."""
        loader1 = get_template_loader()
        loader2 = get_template_loader()
        assert loader1 is loader2
