"""Export API endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from research_tool.core.logging import get_logger
from research_tool.services.export import ExportFormat, ResearchExportData
from research_tool.services.export.docx import DOCXExporter
from research_tool.services.export.json_export import JSONExporter
from research_tool.services.export.markdown import MarkdownExporter
from research_tool.services.export.pdf import PDFExporter
from research_tool.services.export.pptx import PPTXExporter
from research_tool.services.export.xlsx import XLSXExporter

logger = get_logger(__name__)

router = APIRouter(prefix="/api/export", tags=["export"])

# Available exporters
EXPORTERS = {
    ExportFormat.MARKDOWN: MarkdownExporter(),
    ExportFormat.JSON: JSONExporter(),
    ExportFormat.PDF: PDFExporter(),
    ExportFormat.DOCX: DOCXExporter(),
    ExportFormat.PPTX: PPTXExporter(),
    ExportFormat.XLSX: XLSXExporter(),
}


class ExportRequest(BaseModel):
    """Request body for export endpoint."""

    format: str
    query: str
    domain: str
    summary: str
    facts: list[dict[str, object]]
    sources: list[dict[str, object]]
    confidence_score: float
    limitations: list[str]
    metadata: dict[str, object] = {}


class ExportFormatInfo(BaseModel):
    """Information about an export format."""

    format: str
    mime_type: str
    file_extension: str
    description: str


@router.get("/formats")
async def get_export_formats() -> list[ExportFormatInfo]:
    """Get list of available export formats.

    Returns:
        list[ExportFormatInfo]: Available formats with metadata
    """
    formats = [
        ExportFormatInfo(
            format="markdown",
            mime_type="text/markdown",
            file_extension="md",
            description="Markdown document for easy reading and editing",
        ),
        ExportFormatInfo(
            format="json",
            mime_type="application/json",
            file_extension="json",
            description="Structured JSON for programmatic access",
        ),
        ExportFormatInfo(
            format="pdf",
            mime_type="application/pdf",
            file_extension="pdf",
            description="PDF document for printing and sharing",
        ),
        ExportFormatInfo(
            format="docx",
            mime_type=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
            file_extension="docx",
            description="Microsoft Word document",
        ),
        ExportFormatInfo(
            format="pptx",
            mime_type=(
                "application/vnd.openxmlformats-officedocument"
                ".presentationml.presentation"
            ),
            file_extension="pptx",
            description="Microsoft PowerPoint presentation",
        ),
        ExportFormatInfo(
            format="xlsx",
            mime_type=(
                "application/vnd.openxmlformats-officedocument"
                ".spreadsheetml.sheet"
            ),
            file_extension="xlsx",
            description="Microsoft Excel spreadsheet",
        ),
    ]

    logger.info("export_formats_requested", count=len(formats))
    return formats


@router.post("")
async def export_research(request: ExportRequest) -> Response:
    """Export research results to specified format.

    Args:
        request: Export request with format and research data

    Returns:
        Response: File download response

    Raises:
        HTTPException: If format is invalid or export fails
    """
    # Validate format
    try:
        export_format = ExportFormat(request.format.lower())
    except ValueError as e:
        valid_formats = [f.value for f in ExportFormat]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format '{request.format}'. "
            f"Valid formats: {valid_formats}",
        ) from e

    # Get exporter
    exporter = EXPORTERS.get(export_format)
    if not exporter:
        raise HTTPException(
            status_code=500, detail=f"Exporter not configured for {export_format.value}"
        )

    # Create export data
    export_data = ResearchExportData(
        query=request.query,
        domain=request.domain,
        summary=request.summary,
        facts=request.facts,
        sources=request.sources,
        confidence_score=request.confidence_score,
        limitations=request.limitations,
        metadata=request.metadata,
    )

    logger.info(
        "export_request",
        format=export_format.value,
        query=request.query[:50],
        facts_count=len(request.facts),
        sources_count=len(request.sources),
    )

    # Export
    result = await exporter.export(export_data)

    if not result.success:
        logger.error("export_failed", format=export_format.value, error=result.error)
        raise HTTPException(status_code=500, detail=f"Export failed: {result.error}")

    # Prepare response
    content = result.content
    if isinstance(content, str):
        content = content.encode("utf-8")

    logger.info(
        "export_success",
        format=export_format.value,
        filename=result.filename,
        size_bytes=len(content) if content else 0,
    )

    return Response(
        content=content,
        media_type=result.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
        },
    )
