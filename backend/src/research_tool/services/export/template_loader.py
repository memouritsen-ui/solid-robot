"""Template loading and rendering for exports."""

from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from research_tool.services.export.exporter import ResearchExportData


class TemplateLoader:
    """Load and render Jinja2 templates for exports.

    Supports template selection based on export format and optional
    domain-specific templates.
    """

    def __init__(self, template_dir: Path | None = None):
        """Initialize the template loader.

        Args:
            template_dir: Directory containing templates. Defaults to
                         backend/templates/
        """
        if template_dir is None:
            # Default to backend/templates/ relative to this file
            # Path: export/services/research_tool/src -> backend/templates
            template_dir = (
                Path(__file__).parent.parent.parent.parent.parent / "templates"
            )

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def get_template_name(
        self, format_name: str, domain: str | None = None
    ) -> str:
        """Get the template name for a format, with optional domain override.

        Template selection priority:
        1. report.{domain}.{format}.j2 (domain-specific)
        2. report.{format}.j2 (default)

        Args:
            format_name: Export format (md, html, etc.)
            domain: Optional domain for domain-specific templates

        Returns:
            str: Template filename to use
        """
        if domain:
            domain_template = f"report.{domain.lower()}.{format_name}.j2"
            if (self.template_dir / domain_template).exists():
                return domain_template

        return f"report.{format_name}.j2"

    def render(
        self,
        format_name: str,
        data: ResearchExportData,
        extra_context: dict[str, Any] | None = None,
    ) -> str:
        """Render a template with research data.

        Args:
            format_name: Export format (md, html)
            data: Research data to render
            extra_context: Optional additional template context

        Returns:
            str: Rendered template content

        Raises:
            jinja2.TemplateNotFound: If template doesn't exist
        """
        template_name = self.get_template_name(format_name, data.domain)
        template = self.env.get_template(template_name)

        context = {
            "query": data.query,
            "domain": data.domain,
            "summary": data.summary,
            "facts": data.facts,
            "sources": data.sources,
            "confidence_score": data.confidence_score,
            "limitations": data.limitations,
            "metadata": data.metadata,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            # Anti-pattern prevention fields
            "not_found": data.not_found,
            "stopping_reason": data.stopping_reason,
            "access_failures": data.access_failures,
        }

        if extra_context:
            context.update(extra_context)

        return template.render(**context)

    def render_markdown(self, data: ResearchExportData) -> str:
        """Render research data to Markdown.

        Args:
            data: Research data

        Returns:
            str: Markdown content
        """
        return self.render("md", data)

    def render_html(self, data: ResearchExportData) -> str:
        """Render research data to HTML.

        Args:
            data: Research data

        Returns:
            str: HTML content
        """
        return self.render("html", data)


# Global instance for convenience
_loader: TemplateLoader | None = None


def get_template_loader() -> TemplateLoader:
    """Get the global template loader instance.

    Returns:
        TemplateLoader: Shared template loader
    """
    global _loader
    if _loader is None:
        _loader = TemplateLoader()
    return _loader
