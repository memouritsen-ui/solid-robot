"""PDF export provider using WeasyPrint."""

from datetime import datetime
from io import BytesIO
from pathlib import Path

from weasyprint import HTML

from .exporter import Exporter, ExportFormat, ExportResult, ResearchExportData


class PDFExporter(Exporter):
    """Export research results to PDF format using WeasyPrint."""

    def __init__(self, template_dir: Path | None = None):
        """Initialize PDF exporter.

        Args:
            template_dir: Directory containing HTML templates
        """
        self.template_dir = template_dir

    @property
    def format(self) -> ExportFormat:
        """Return the export format."""
        return ExportFormat.PDF

    @property
    def mime_type(self) -> str:
        """Return the MIME type."""
        return "application/pdf"

    @property
    def file_extension(self) -> str:
        """Return the file extension."""
        return "pdf"

    async def export(self, data: ResearchExportData) -> ExportResult:
        """Export research data to PDF.

        Args:
            data: Research data to export

        Returns:
            ExportResult: PDF content as bytes
        """
        try:
            html_content = self._generate_html(data)
            pdf_bytes = self._render_pdf(html_content)

            return ExportResult(
                success=True,
                format=self.format,
                content=pdf_bytes,
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

    def _generate_html(self, data: ResearchExportData) -> str:
        """Generate HTML content for PDF rendering.

        Args:
            data: Research data

        Returns:
            str: HTML content
        """
        # Escape HTML entities
        def escape(text: str) -> str:
            """Escape HTML special characters to prevent XSS."""
            return (
                text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )

        facts_html = ""
        for i, fact in enumerate(data.facts, 1):
            statement = escape(fact.get("statement", fact.get("content", "")))
            confidence = fact.get("confidence", 0.0)
            source = escape(fact.get("source", "Unknown"))
            facts_html += f"""
            <div class="fact">
                <h3>Finding {i}</h3>
                <blockquote>{statement}</blockquote>
                <p><strong>Confidence:</strong> {confidence:.1%} |
                   <strong>Source:</strong> {source}</p>
            </div>
            """

        sources_html = ""
        for _i, src_item in enumerate(data.sources, 1):
            title = escape(src_item.get("title", "Untitled"))
            url = src_item.get("url", "")
            source_type = src_item.get("type", "web")
            sources_html += f"""
            <li>
                <strong>{title}</strong><br>
                <span class="url">{escape(url)}</span><br>
                <span class="type">Type: {source_type}</span>
            </li>
            """

        limitations_html = ""
        for limitation in data.limitations:
            limitations_html += f"<li>{escape(limitation)}</li>"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1 {{
                    color: #333;
                    border-bottom: 2px solid #4A90D9;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #4A90D9;
                    margin-top: 30px;
                }}
                .metadata {{
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .fact {{
                    margin-bottom: 20px;
                    padding: 15px;
                    background: #fafafa;
                    border-left: 4px solid #4A90D9;
                }}
                blockquote {{
                    margin: 10px 0;
                    font-style: italic;
                }}
                .limitations {{
                    background: #fff3cd;
                    padding: 15px;
                    border-radius: 5px;
                }}
                .url {{
                    color: #666;
                    font-size: 0.9em;
                    word-break: break-all;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 0.9em;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <h1>Research Report: {escape(data.query)}</h1>

            <div class="metadata">
                <p><strong>Domain:</strong> {escape(data.domain)}</p>
                <p><strong>Confidence Score:</strong> {data.confidence_score:.1%}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>

            <h2>Executive Summary</h2>
            <p>{escape(data.summary)}</p>

            <h2>Key Findings</h2>
            {facts_html}

            <h2>Sources</h2>
            <ol>
                {sources_html}
            </ol>

            <h2>Limitations</h2>
            <div class="limitations">
                <p>This research has the following limitations:</p>
                <ul>
                    {limitations_html}
                </ul>
            </div>

            <div class="footer">
                <p>This report was generated automatically.
                Please verify critical information from primary sources.</p>
            </div>
        </body>
        </html>
        """

        return html

    def _render_pdf(self, html_content: str) -> bytes:
        """Render HTML to PDF.

        Args:
            html_content: HTML string

        Returns:
            bytes: PDF content
        """
        buffer = BytesIO()
        HTML(string=html_content).write_pdf(buffer)
        return buffer.getvalue()
