"""Abstract base class for export providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ExportFormat(Enum):
    """Supported export formats."""

    MARKDOWN = "markdown"
    JSON = "json"
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"


@dataclass
class ExportResult:
    """Result of an export operation.

    Attributes:
        success: Whether export succeeded
        format: Export format used
        content: Export content (bytes for binary, str for text)
        filename: Suggested filename
        mime_type: MIME type for download
        error: Error message if failed
    """

    success: bool
    format: ExportFormat
    content: bytes | str | None
    filename: str
    mime_type: str
    error: str | None = None

    @property
    def is_binary(self) -> bool:
        """Check if content is binary."""
        return self.format in (
            ExportFormat.PDF,
            ExportFormat.DOCX,
            ExportFormat.PPTX,
            ExportFormat.XLSX,
        )


@dataclass
class ResearchExportData:
    """Data structure for research results to export.

    Attributes:
        query: Original research query
        domain: Detected domain
        summary: Executive summary
        facts: List of extracted facts
        sources: List of source references
        confidence_score: Overall confidence score
        limitations: Known limitations
        metadata: Additional metadata
    """

    query: str
    domain: str
    summary: str
    facts: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    confidence_score: float
    limitations: list[str]
    metadata: dict[str, Any]


class Exporter(ABC):
    """Abstract base class for export providers.

    All exporters must implement the export() method.
    """

    @property
    @abstractmethod
    def format(self) -> ExportFormat:
        """Return the export format this exporter handles."""
        ...

    @property
    @abstractmethod
    def mime_type(self) -> str:
        """Return the MIME type for this format."""
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format."""
        ...

    @abstractmethod
    async def export(self, data: ResearchExportData) -> ExportResult:
        """Export research data to the target format.

        Args:
            data: Research data to export

        Returns:
            ExportResult: Result containing content or error
        """
        ...

    def generate_filename(self, query: str) -> str:
        """Generate a filename from query.

        Args:
            query: Research query

        Returns:
            str: Sanitized filename with extension
        """
        # Sanitize query for filename
        safe_query = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_"
            for c in query[:50]
        ).strip()
        safe_query = safe_query.replace(" ", "_")

        return f"research_{safe_query}.{self.file_extension}"
