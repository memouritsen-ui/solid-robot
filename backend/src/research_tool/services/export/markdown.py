"""Markdown export provider."""

from datetime import datetime

from .exporter import Exporter, ExportFormat, ExportResult, ResearchExportData


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
            content = self._generate_markdown(data)
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

    def _generate_markdown(self, data: ResearchExportData) -> str:
        """Generate Markdown content from research data.

        Args:
            data: Research data

        Returns:
            str: Markdown content
        """
        lines: list[str] = []

        # Title
        lines.append(f"# Research Report: {data.query}")
        lines.append("")

        # Metadata
        lines.append("## Metadata")
        lines.append("")
        lines.append(f"- **Domain**: {data.domain}")
        lines.append(f"- **Confidence Score**: {data.confidence_score:.1%}")
        lines.append(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(data.summary)
        lines.append("")

        # Key Findings
        if data.facts:
            lines.append("## Key Findings")
            lines.append("")
            for i, fact in enumerate(data.facts, 1):
                statement = fact.get("statement", fact.get("content", ""))
                confidence = fact.get("confidence", 0.0)
                source = fact.get("source", "Unknown")
                lines.append(f"### Finding {i}")
                lines.append("")
                lines.append(f"> {statement}")
                lines.append("")
                lines.append(f"- **Confidence**: {confidence:.1%}")
                lines.append(f"- **Source**: {source}")
                lines.append("")

        # Sources
        if data.sources:
            lines.append("## Sources")
            lines.append("")
            for i, source in enumerate(data.sources, 1):
                title = source.get("title", "Untitled")
                url = source.get("url", "")
                source_type = source.get("type", "web")
                lines.append(f"{i}. **{title}**")
                if url:
                    lines.append(f"   - URL: [{url}]({url})")
                lines.append(f"   - Type: {source_type}")
                lines.append("")

        # Limitations
        if data.limitations:
            lines.append("## Limitations")
            lines.append("")
            lines.append(
                "This research has the following limitations that should be "
                "considered when interpreting the results:"
            )
            lines.append("")
            for limitation in data.limitations:
                lines.append(f"- {limitation}")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(
            "*This report was generated automatically. "
            "Please verify critical information from primary sources.*"
        )

        return "\n".join(lines)
