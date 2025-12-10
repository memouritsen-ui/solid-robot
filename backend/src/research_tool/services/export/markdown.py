"""Markdown export provider."""

from .exporter import Exporter, ExportFormat, ExportResult, ResearchExportData
from .template_loader import get_template_loader


class MarkdownExporter(Exporter):
    """Export research results to Markdown format."""

    @property
    def format(self) -> ExportFormat:
        """Return the export format."""
        return ExportFormat.MARKDOWN

    @property
    def mime_type(self) -> str:
        """Return the MIME type."""
        return "text/markdown"

    @property
    def file_extension(self) -> str:
        """Return the file extension."""
        return "md"

    async def export(self, data: ResearchExportData) -> ExportResult:
        """Export research data to Markdown.

        Args:
            data: Research data to export

        Returns:
            ExportResult: Markdown content
        """
        try:
            loader = get_template_loader()
            content = loader.render_markdown(data)
            return ExportResult(
                success=True,
                format=self.format,
                content=content,
                filename=self.generate_filename(data.query),
                mime_type=self.mime_type,
            )
        except Exception as e:
            return ExportResult(
                success=False,
                format=self.format,
                content=None,
                filename=self.generate_filename(data.query),
                mime_type=self.mime_type,
                error=str(e),
            )
