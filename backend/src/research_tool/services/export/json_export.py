"""JSON export provider."""

import json
from datetime import datetime
from typing import Any

from .exporter import Exporter, ExportFormat, ExportResult, ResearchExportData


class JSONExporter(Exporter):
    """Export research results to JSON format."""

    @property
    def format(self) -> ExportFormat:
        """Return the export format."""
        return ExportFormat.JSON

    @property
    def mime_type(self) -> str:
        """Return the MIME type."""
        return "application/json"

    @property
    def file_extension(self) -> str:
        """Return the file extension."""
        return "json"

    async def export(self, data: ResearchExportData) -> ExportResult:
        """Export research data to JSON.

        Args:
            data: Research data to export

        Returns:
            ExportResult: JSON content
        """
        try:
            content = self._generate_json(data)
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

    def _generate_json(self, data: ResearchExportData) -> str:
        """Generate JSON content from research data.

        Args:
            data: Research data

        Returns:
            str: JSON content
        """
        export_data: dict[str, Any] = {
            "research_report": {
                "query": data.query,
                "domain": data.domain,
                "generated_at": datetime.now().isoformat(),
                "confidence_score": data.confidence_score,
            },
            "summary": data.summary,
            "facts": [
                {
                    "statement": fact.get("statement", fact.get("content", "")),
                    "confidence": fact.get("confidence", 0.0),
                    "source": fact.get("source", "Unknown"),
                    "verified": fact.get("verified", False),
                }
                for fact in data.facts
            ],
            "sources": [
                {
                    "title": source.get("title", "Untitled"),
                    "url": source.get("url", ""),
                    "type": source.get("type", "web"),
                    "accessed_at": source.get("accessed_at", ""),
                    "reliability_score": source.get("reliability_score", 0.0),
                }
                for source in data.sources
            ],
            "limitations": data.limitations,
            "metadata": data.metadata,
        }

        return json.dumps(export_data, indent=2, ensure_ascii=False)
