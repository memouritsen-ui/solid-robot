# PHASE 6: EXPORT SYSTEM
## Detailed Implementation Guide

**Prerequisites**: 
- Phase 5 complete and validated
- Branch: `git checkout -b phase-6-export develop`

**Tasks**: TODO.md #240-270

**Estimated Duration**: 2-3 hours

---

## 1. OBJECTIVES

By the end of Phase 6:
- [ ] All export formats working (MD, JSON, PDF, DOCX, PPTX, XLSX)
- [ ] Jinja2 templates for each format
- [ ] Template selection based on context
- [ ] Reports include what was NOT found
- [ ] Reports include stopping rationale
- [ ] Export API operational
- [ ] SwiftUI export view functional

---

## 2. EXPORT INTERFACE

### 2.1 Abstract Interface

**File**: `/backend/src/research_tool/services/export/exporter.py`

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class Exporter(ABC):
    """Abstract interface for export formats."""
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Human-readable format name."""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension (e.g., '.pdf')."""
        pass
    
    @property
    @abstractmethod
    def mime_type(self) -> str:
        """MIME type for HTTP response."""
        pass
    
    @abstractmethod
    async def export(
        self,
        research_result: dict,
        output_path: Path,
        options: Optional[dict] = None
    ) -> Path:
        """
        Export research results to file.
        
        Args:
            research_result: Complete research output
            output_path: Where to save the file
            options: Format-specific options
            
        Returns:
            Path to created file
        """
        pass
```

---

## 3. MARKDOWN EXPORT

### 3.1 Implementation

**File**: `/backend/src/research_tool/services/export/markdown.py`

```python
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .exporter import Exporter


class MarkdownExporter(Exporter):
    """Export to Markdown format."""
    
    @property
    def format_name(self) -> str:
        return "Markdown"
    
    @property
    def file_extension(self) -> str:
        return ".md"
    
    @property
    def mime_type(self) -> str:
        return "text/markdown"
    
    def __init__(self, template_dir: str = "./templates"):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template("report.md.j2")
    
    async def export(
        self,
        research_result: dict,
        output_path: Path,
        options: dict = None
    ) -> Path:
        """Export to Markdown."""
        
        # Prepare template context
        context = self._prepare_context(research_result)
        
        # Render template
        content = self.template.render(**context)
        
        # Write file
        output_path.write_text(content)
        
        return output_path
    
    def _prepare_context(self, result: dict) -> dict:
        """Prepare template context from research result."""
        return {
            "title": result.get("query", "Research Report"),
            "date": result.get("completed_at", ""),
            "summary": result.get("summary", ""),
            "findings": result.get("findings", []),
            "entities": result.get("entities", []),
            "facts": result.get("facts", []),
            "sources": result.get("sources", []),
            
            # CRITICAL: Include limitations (Anti-Pattern #11)
            "limitations": result.get("limitations", []),
            "not_found": result.get("not_found", []),
            
            # CRITICAL: Include stopping rationale (Anti-Pattern #12)
            "stopping_reason": result.get("stopping_reason", ""),
            "saturation_metrics": result.get("saturation_metrics", {}),
            
            "confidence_scores": result.get("confidence_scores", {}),
            "access_failures": result.get("access_failures", [])
        }
```

### 3.2 Markdown Template

**File**: `/backend/templates/report.md.j2`

```jinja2
# {{ title }}

**Generated:** {{ date }}

---

## Executive Summary

{{ summary }}

---

## Key Findings

{% for finding in findings %}
### {{ loop.index }}. {{ finding.title }}

{{ finding.content }}

**Confidence:** {{ finding.confidence | default("N/A") }}

{% endfor %}

---

## Entities Identified

| Entity | Type | Mentions | Confidence |
|--------|------|----------|------------|
{% for entity in entities %}
| {{ entity.name }} | {{ entity.type }} | {{ entity.mentions }} | {{ entity.confidence | round(2) }} |
{% endfor %}

---

## Verified Facts

{% for fact in facts %}
- **{{ fact.statement }}**
  - Confidence: {{ (fact.confidence * 100) | round }}%
  - Sources: {{ fact.sources | join(", ") }}
  {% if fact.contradictions %}
  - ⚠️ Contradictions found: {{ fact.contradictions | join("; ") }}
  {% endif %}
{% endfor %}

---

## Sources Consulted

{% for source in sources %}
{{ loop.index }}. [{{ source.title }}]({{ source.url }})
   - Source: {{ source.source_name }}
   - Quality: {{ source.quality_score | round(2) }}
{% endfor %}

---

## Limitations and Gaps

{% if not_found %}
### Information Not Found

The following topics could not be adequately researched:

{% for item in not_found %}
- {{ item.topic }}: {{ item.reason }}
{% endfor %}
{% endif %}

{% if limitations %}
### Research Limitations

{% for limitation in limitations %}
- {{ limitation }}
{% endfor %}
{% endif %}

{% if access_failures %}
### Access Issues

The following sources could not be accessed:

{% for failure in access_failures %}
- {{ failure.url }} ({{ failure.error_type }})
{% endfor %}
{% endif %}

---

## Research Completion

**Stopping Reason:** {{ stopping_reason }}

**Saturation Metrics:**
- New entities ratio: {{ saturation_metrics.new_entities_ratio | default("N/A") }}
- New facts ratio: {{ saturation_metrics.new_facts_ratio | default("N/A") }}
- Source coverage: {{ saturation_metrics.source_coverage | default("N/A") }}

---

*This report was generated by Research Tool. Verify critical facts independently.*
```

---

## 4. JSON EXPORT

**File**: `/backend/src/research_tool/services/export/json_export.py`

```python
import json
from pathlib import Path
from datetime import datetime
from .exporter import Exporter


class JSONExporter(Exporter):
    """Export to JSON format."""
    
    @property
    def format_name(self) -> str:
        return "JSON"
    
    @property
    def file_extension(self) -> str:
        return ".json"
    
    @property
    def mime_type(self) -> str:
        return "application/json"
    
    async def export(
        self,
        research_result: dict,
        output_path: Path,
        options: dict = None
    ) -> Path:
        """Export to JSON."""
        
        # Add metadata
        output = {
            "metadata": {
                "format_version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "tool": "Research Tool"
            },
            "research": research_result
        }
        
        # Pretty print option
        indent = options.get("indent", 2) if options else 2
        
        # Write file
        output_path.write_text(json.dumps(output, indent=indent, default=str))
        
        return output_path
```

---

## 5. PDF EXPORT

**File**: `/backend/src/research_tool/services/export/pdf.py`

```python
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from .exporter import Exporter


class PDFExporter(Exporter):
    """Export to PDF format using WeasyPrint."""
    
    @property
    def format_name(self) -> str:
        return "PDF"
    
    @property
    def file_extension(self) -> str:
        return ".pdf"
    
    @property
    def mime_type(self) -> str:
        return "application/pdf"
    
    def __init__(self, template_dir: str = "./templates"):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template("report.html.j2")
    
    async def export(
        self,
        research_result: dict,
        output_path: Path,
        options: dict = None
    ) -> Path:
        """Export to PDF via HTML."""
        
        # Prepare context (same as Markdown)
        context = self._prepare_context(research_result)
        
        # Render HTML
        html_content = self.template.render(**context)
        
        # Convert to PDF
        HTML(string=html_content).write_pdf(output_path)
        
        return output_path
```

---

## 6. DOCX EXPORT

**File**: `/backend/src/research_tool/services/export/docx.py`

```python
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.style import WD_STYLE_TYPE
from .exporter import Exporter


class DOCXExporter(Exporter):
    """Export to Word format."""
    
    @property
    def format_name(self) -> str:
        return "Word Document"
    
    @property
    def file_extension(self) -> str:
        return ".docx"
    
    @property
    def mime_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    async def export(
        self,
        research_result: dict,
        output_path: Path,
        options: dict = None
    ) -> Path:
        """Export to DOCX."""
        
        doc = Document()
        
        # Title
        doc.add_heading(research_result.get("query", "Research Report"), 0)
        
        # Summary
        doc.add_heading("Executive Summary", level=1)
        doc.add_paragraph(research_result.get("summary", ""))
        
        # Findings
        doc.add_heading("Key Findings", level=1)
        for i, finding in enumerate(research_result.get("findings", []), 1):
            doc.add_heading(f"{i}. {finding.get('title', '')}", level=2)
            doc.add_paragraph(finding.get("content", ""))
        
        # CRITICAL: Limitations section
        doc.add_heading("Limitations and Gaps", level=1)
        
        not_found = research_result.get("not_found", [])
        if not_found:
            doc.add_heading("Information Not Found", level=2)
            for item in not_found:
                doc.add_paragraph(f"• {item['topic']}: {item['reason']}", style="List Bullet")
        
        # CRITICAL: Stopping rationale
        doc.add_heading("Research Completion", level=1)
        doc.add_paragraph(f"Stopping Reason: {research_result.get('stopping_reason', 'N/A')}")
        
        # Save
        doc.save(output_path)
        
        return output_path
```

---

## 7. PPTX EXPORT

**File**: `/backend/src/research_tool/services/export/pptx.py`

```python
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from .exporter import Exporter


class PPTXExporter(Exporter):
    """Export to PowerPoint format."""
    
    @property
    def format_name(self) -> str:
        return "PowerPoint"
    
    @property
    def file_extension(self) -> str:
        return ".pptx"
    
    @property
    def mime_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    
    async def export(
        self,
        research_result: dict,
        output_path: Path,
        options: dict = None
    ) -> Path:
        """Export to PPTX."""
        
        prs = Presentation()
        
        # Title slide
        title_slide = prs.slides.add_slide(prs.slide_layouts[0])
        title_slide.shapes.title.text = research_result.get("query", "Research Report")
        title_slide.placeholders[1].text = f"Generated: {research_result.get('completed_at', '')}"
        
        # Summary slide
        summary_slide = prs.slides.add_slide(prs.slide_layouts[1])
        summary_slide.shapes.title.text = "Executive Summary"
        summary_slide.placeholders[1].text = research_result.get("summary", "")
        
        # Finding slides (one per finding)
        for finding in research_result.get("findings", [])[:5]:  # Max 5 findings
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            slide.shapes.title.text = finding.get("title", "")
            slide.placeholders[1].text = finding.get("content", "")[:500]  # Truncate
        
        # Limitations slide (CRITICAL)
        limitations_slide = prs.slides.add_slide(prs.slide_layouts[1])
        limitations_slide.shapes.title.text = "Limitations & Gaps"
        
        limitations_text = []
        for item in research_result.get("not_found", []):
            limitations_text.append(f"• {item['topic']}: {item['reason']}")
        
        limitations_slide.placeholders[1].text = "\n".join(limitations_text) or "No significant gaps identified."
        
        # Save
        prs.save(output_path)
        
        return output_path
```

---

## 8. XLSX EXPORT

**File**: `/backend/src/research_tool/services/export/xlsx.py`

```python
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from .exporter import Exporter


class XLSXExporter(Exporter):
    """Export to Excel format."""
    
    @property
    def format_name(self) -> str:
        return "Excel"
    
    @property
    def file_extension(self) -> str:
        return ".xlsx"
    
    @property
    def mime_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    async def export(
        self,
        research_result: dict,
        output_path: Path,
        options: dict = None
    ) -> Path:
        """Export to XLSX."""
        
        wb = Workbook()
        
        # Summary sheet
        ws_summary = wb.active
        ws_summary.title = "Summary"
        ws_summary["A1"] = "Research Query"
        ws_summary["B1"] = research_result.get("query", "")
        ws_summary["A2"] = "Generated"
        ws_summary["B2"] = research_result.get("completed_at", "")
        ws_summary["A4"] = "Summary"
        ws_summary["A5"] = research_result.get("summary", "")
        
        # Entities sheet
        ws_entities = wb.create_sheet("Entities")
        ws_entities.append(["Entity", "Type", "Mentions", "Confidence", "Sources"])
        for entity in research_result.get("entities", []):
            ws_entities.append([
                entity.get("name", ""),
                entity.get("type", ""),
                entity.get("mentions", 0),
                entity.get("confidence", 0),
                ", ".join(entity.get("sources", []))
            ])
        
        # Facts sheet
        ws_facts = wb.create_sheet("Facts")
        ws_facts.append(["Fact", "Confidence", "Verified", "Sources", "Contradictions"])
        for fact in research_result.get("facts", []):
            ws_facts.append([
                fact.get("statement", ""),
                fact.get("confidence", 0),
                "Yes" if fact.get("verified") else "No",
                ", ".join(fact.get("sources", [])),
                ", ".join(fact.get("contradictions", []))
            ])
        
        # Sources sheet
        ws_sources = wb.create_sheet("Sources")
        ws_sources.append(["Title", "URL", "Source", "Quality"])
        for source in research_result.get("sources", []):
            ws_sources.append([
                source.get("title", ""),
                source.get("url", ""),
                source.get("source_name", ""),
                source.get("quality_score", 0)
            ])
        
        # Limitations sheet (CRITICAL)
        ws_limits = wb.create_sheet("Limitations")
        ws_limits.append(["Topic", "Reason"])
        for item in research_result.get("not_found", []):
            ws_limits.append([item.get("topic", ""), item.get("reason", "")])
        
        ws_limits.append([])
        ws_limits.append(["Stopping Reason", research_result.get("stopping_reason", "")])
        
        # Save
        wb.save(output_path)
        
        return output_path
```

---

## 9. EXPORT API

**File**: `/backend/src/research_tool/api/routes/export.py`

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import uuid

from research_tool.services.export import (
    MarkdownExporter, JSONExporter, PDFExporter,
    DOCXExporter, PPTXExporter, XLSXExporter
)

router = APIRouter(prefix="/api/export", tags=["export"])

EXPORTERS = {
    "markdown": MarkdownExporter(),
    "json": JSONExporter(),
    "pdf": PDFExporter(),
    "docx": DOCXExporter(),
    "pptx": PPTXExporter(),
    "xlsx": XLSXExporter()
}


@router.get("/formats")
async def list_formats():
    """List available export formats."""
    return [
        {
            "id": key,
            "name": exp.format_name,
            "extension": exp.file_extension
        }
        for key, exp in EXPORTERS.items()
    ]


@router.post("")
async def export_research(
    session_id: str,
    format: str,
    options: dict = None
):
    """Export research results."""
    
    if format not in EXPORTERS:
        raise HTTPException(400, f"Unknown format: {format}")
    
    # Get research result
    if session_id not in active_sessions:
        raise HTTPException(404, "Session not found")
    
    result = active_sessions[session_id].get("result")
    if not result:
        raise HTTPException(400, "Research not complete")
    
    # Generate output path
    exporter = EXPORTERS[format]
    output_dir = Path("./data/exports")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{session_id}{exporter.file_extension}"
    
    # Export
    await exporter.export(result, output_path, options)
    
    return FileResponse(
        output_path,
        media_type=exporter.mime_type,
        filename=f"research_report{exporter.file_extension}"
    )
```

---

## 10. SWIFTUI EXPORT VIEW

**File**: `/gui/.../Views/ExportView.swift`

```swift
import SwiftUI

struct ExportView: View {
    @State private var selectedFormat: String = "markdown"
    @State private var isExporting: Bool = false
    @State private var exportSuccess: Bool = false
    
    let sessionId: String
    let formats = [
        ("markdown", "Markdown (.md)"),
        ("json", "JSON (.json)"),
        ("pdf", "PDF (.pdf)"),
        ("docx", "Word (.docx)"),
        ("pptx", "PowerPoint (.pptx)"),
        ("xlsx", "Excel (.xlsx)")
    ]
    
    var body: some View {
        Form {
            Section("Export Format") {
                Picker("Format", selection: $selectedFormat) {
                    ForEach(formats, id: \.0) { format in
                        Text(format.1).tag(format.0)
                    }
                }
                .pickerStyle(.radioGroup)
            }
            
            Section {
                Button(action: exportReport) {
                    HStack {
                        if isExporting {
                            ProgressView()
                                .scaleEffect(0.7)
                        }
                        Text(isExporting ? "Exporting..." : "Export Report")
                    }
                }
                .disabled(isExporting)
            }
            
            if exportSuccess {
                Section {
                    Label("Export successful!", systemImage: "checkmark.circle.fill")
                        .foregroundColor(.green)
                }
            }
        }
        .navigationTitle("Export")
    }
    
    private func exportReport() {
        isExporting = true
        
        Task {
            do {
                let url = URL(string: "http://localhost:8000/api/export")!
                var request = URLRequest(url: url)
                request.httpMethod = "POST"
                request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                
                let body = ["session_id": sessionId, "format": selectedFormat]
                request.httpBody = try JSONEncoder().encode(body)
                
                let (data, response) = try await URLSession.shared.data(for: request)
                
                // Save file
                if let httpResponse = response as? HTTPURLResponse,
                   httpResponse.statusCode == 200 {
                    let savePanel = NSSavePanel()
                    savePanel.allowedContentTypes = [.data]
                    savePanel.nameFieldStringValue = "research_report.\(selectedFormat)"
                    
                    if savePanel.runModal() == .OK, let url = savePanel.url {
                        try data.write(to: url)
                        exportSuccess = true
                    }
                }
            } catch {
                print("Export error: \(error)")
            }
            
            isExporting = false
        }
    }
}
```

---

## 11. ANTI-PATTERN PREVENTION

### 11.1 Anti-Pattern #11: Omitting What Wasn't Found

Every export template MUST include:

```jinja2
## Limitations and Gaps

{% if not_found %}
### Information Not Found

{% for item in not_found %}
- {{ item.topic }}: {{ item.reason }}
{% endfor %}
{% else %}
No significant gaps identified in this research.
{% endif %}
```

### 11.2 Anti-Pattern #12: Not Explaining Stopping Rationale

Every export template MUST include:

```jinja2
## Research Completion

**Stopping Reason:** {{ stopping_reason }}

This research was concluded because {{ stopping_reason | lower }}.
```

---

## 12. TESTS

```python
async def test_markdown_export_valid():
    """Markdown export produces valid file."""
    exporter = MarkdownExporter()
    result = await exporter.export(sample_result, Path("/tmp/test.md"))
    assert result.exists()
    content = result.read_text()
    assert "# " in content  # Has heading
    assert "Limitations" in content  # Anti-pattern #11

async def test_pdf_export_opens():
    """PDF export produces openable file."""
    exporter = PDFExporter()
    result = await exporter.export(sample_result, Path("/tmp/test.pdf"))
    assert result.exists()
    assert result.stat().st_size > 0

async def test_all_exports_include_limitations():
    """All export formats include limitations section."""
    for name, exporter in EXPORTERS.items():
        result = await exporter.export(sample_result, Path(f"/tmp/test{exporter.file_extension}"))
        # Format-specific checks...

async def test_large_export_handles_1000_sources():
    """Large export doesn't crash."""
    large_result = {**sample_result, "sources": [sample_source] * 1000}
    for exporter in EXPORTERS.values():
        await exporter.export(large_result, Path(f"/tmp/large{exporter.file_extension}"))
```

---

## 13. VALIDATION GATE

```
□ Markdown export valid
□ JSON export valid
□ PDF export opens correctly
□ DOCX export opens correctly
□ PPTX export opens correctly  
□ XLSX export opens correctly
□ All formats include limitations (Anti-Pattern #11)
□ All formats include stopping reason (Anti-Pattern #12)
□ Large export (1000 sources) doesn't crash
□ SwiftUI export view works
```

---

## 14. COMMIT AND MERGE

```bash
git add .
git commit -m "feat: complete phase 6 export system [BUILD-PLAN Phase 6]"
git checkout develop
git merge phase-6-export
git push origin develop
```

---

*END OF PHASE 6 GUIDE*
