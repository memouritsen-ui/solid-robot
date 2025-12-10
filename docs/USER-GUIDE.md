# Research Tool User Guide

A step-by-step guide to using the Research Tool for professional-grade research.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Privacy Modes](#privacy-modes)
3. [Running Research](#running-research)
4. [Understanding Results](#understanding-results)
5. [Exporting Reports](#exporting-reports)
6. [Tips for Best Results](#tips-for-best-results)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Starting the Backend

1. Open Terminal
2. Navigate to the project:
   ```bash
   cd ~/solid-robot/backend
   ```
3. Start the server:
   ```bash
   uv run uvicorn src.research_tool.main:app --port 8000
   ```
4. Verify it's running:
   ```bash
   curl http://localhost:8000/api/health
   # Should return: {"status":"healthy","version":"0.1.0"}
   ```

### Starting Ollama (for local models)

1. Ensure Ollama is installed
2. Start Ollama (if not running):
   ```bash
   ollama serve
   ```
3. Verify models are available:
   ```bash
   ollama list
   ```
   Required models:
   - `qwen2.5:32b-instruct-q5_K_M`
   - `llama3.1:8b-instruct-q8_0`

### Opening the GUI

1. Open Xcode
2. Open `gui/ResearchTool/ResearchTool.xcodeproj`
3. Build and run (Cmd+R)

---

## Privacy Modes

Choose your privacy mode based on your needs:

### LOCAL_ONLY

**Best for:** Sensitive queries, confidential data, no internet required

- All LLM processing on your Mac via Ollama
- No data leaves your device
- Slightly slower than cloud models
- Full privacy guaranteed

**When to use:**
- Medical records research
- Competitive intelligence on your company
- Legal research with confidential details
- Offline work

### CLOUD_ALLOWED

**Best for:** Maximum quality, complex queries

- Uses Claude API for best results
- Faster responses
- Higher quality synthesis
- Search queries still go to external APIs

**When to use:**
- General research
- Academic inquiries
- Technical documentation
- When speed matters

### HYBRID (LOCAL_PREFERRED)

**Best for:** Balance of privacy and quality

- Tries local models first
- Falls back to cloud if needed
- Best of both worlds

**When to use:**
- Mixed sensitivity content
- When unsure which mode to use

---

## Running Research

### Via Chat Interface

1. Open the GUI
2. Select your privacy mode from the picker
3. Type your research query
4. Watch the progress in real-time

**Example queries:**
- "What are the current FDA guidelines for diabetes medications?"
- "Compare market share of cloud providers in Europe 2024"
- "Summarize recent research on CRISPR gene editing safety"

### Via API

```bash
# Start research
curl -X POST http://localhost:8000/api/research/start \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest treatments for Type 2 diabetes?",
    "privacy_mode": "LOCAL_ONLY",
    "domain": "medical"
  }'

# Response: {"session_id": "abc-123", ...}

# Check status
curl http://localhost:8000/api/research/abc-123/status
```

### Research Phases

Your research goes through these phases:

| Phase | What Happens | Duration |
|-------|--------------|----------|
| **Clarify** | Understanding your query | ~5s |
| **Plan** | Creating research strategy | ~10s |
| **Collect** | Gathering from sources | ~1-3min |
| **Process** | Extracting information | ~30s |
| **Analyze** | Finding patterns | ~30s |
| **Evaluate** | Checking saturation | ~10s |
| **Synthesize** | Writing report | ~30s |

---

## Understanding Results

### Confidence Scores

Each fact and the overall report has a confidence score:

| Score | Meaning |
|-------|---------|
| 0.9+ | Very high confidence, multiple sources agree |
| 0.7-0.9 | Good confidence, solid evidence |
| 0.5-0.7 | Moderate confidence, some uncertainty |
| <0.5 | Low confidence, limited evidence |

### Source Types

Research draws from multiple source types:

| Type | Examples | Reliability |
|------|----------|-------------|
| **Academic** | PubMed, arXiv, Semantic Scholar | High |
| **Official** | Government sites, .gov | High |
| **News** | Major publications | Medium |
| **Web** | General web results | Variable |

### Saturation Detection

The system knows when to stop researching:
- **New fact rate** drops below 10%
- **Source agreement** reaches 85%+
- **Coverage** of subtopics is complete

---

## Exporting Reports

### Available Formats

| Format | Best For |
|--------|----------|
| **Markdown** | Reading, editing, GitHub |
| **JSON** | Programming, data analysis |
| **PDF** | Printing, formal sharing |
| **DOCX** | Word editing, collaboration |
| **PPTX** | Presentations |
| **XLSX** | Data tables, analysis |

### Via GUI

1. Complete your research
2. Click "Export"
3. Select format
4. Choose save location

### Via API

```bash
curl -X POST http://localhost:8000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "format": "pdf",
    "query": "Diabetes treatments",
    "domain": "medical",
    "summary": "...",
    "facts": [...],
    "sources": [...],
    "confidence_score": 0.85,
    "limitations": ["Limited to English sources"]
  }' \
  --output report.pdf
```

---

## Tips for Best Results

### Writing Good Queries

**Good:**
- "What are the current FDA-approved treatments for Type 2 diabetes, focusing on recent approvals since 2023?"
- "Compare the market positioning of Nvidia, AMD, and Intel in the AI accelerator market as of 2024"

**Less effective:**
- "diabetes treatments" (too vague)
- "nvidia" (not a question)

### Query Components

Include when relevant:
1. **Topic**: What you're researching
2. **Scope**: Time period, geography, industry
3. **Focus**: Specific aspect of interest
4. **Output**: What you need (comparison, summary, analysis)

### Domain Hints

Providing a domain hint improves results:

```json
{
  "query": "...",
  "domain": "medical"  // or: academic, regulatory, competitive_intelligence
}
```

This auto-configures:
- Preferred sources
- Citation style
- Verification standards
- Output format

---

## Troubleshooting

### Backend Won't Start

**Check Python version:**
```bash
python3 --version  # Need 3.11+
```

**Check dependencies:**
```bash
cd backend
uv sync
```

**Check port availability:**
```bash
lsof -i :8000  # Should be empty
```

### Ollama Not Responding

**Check if running:**
```bash
curl http://localhost:11434/api/tags
```

**Restart Ollama:**
```bash
pkill ollama
ollama serve
```

**Pull missing models:**
```bash
ollama pull qwen2.5:32b-instruct-q5_K_M
```

### Slow Research

1. **Check Ollama memory**: May need to restart if using >40GB
2. **Reduce max_sources**: Use 10 instead of 20
3. **Use CLOUD_ALLOWED**: Cloud models are faster
4. **Check network**: Slow searches indicate network issues

### API Key Errors

**Missing Tavily key:**
```
Error: TAVILY_API_KEY not set
```
Fix: Add to `.env` file

**Invalid key:**
```
Error: 401 Unauthorized from Tavily
```
Fix: Verify key at tavily.com

### Export Failures

**PDF export fails:**
```bash
# Install WeasyPrint dependencies
brew install pango gdk-pixbuf libffi
```

**DOCX/PPTX fails:**
```bash
# Reinstall dependencies
uv sync
```

### WebSocket Connection Issues

**Check if backend running:**
```bash
curl http://localhost:8000/api/health
```

**Check CORS:**
- GUI must connect to `localhost:8000`
- Check backend logs for CORS errors

---

## Keyboard Shortcuts (GUI)

| Action | Shortcut |
|--------|----------|
| Send message | Enter |
| New line | Shift+Enter |
| Clear chat | Cmd+K |
| Export | Cmd+E |
| Settings | Cmd+, |

---

## Getting Help

1. Check logs: `backend/logs/research_tool.log`
2. Run tests: `uv run pytest tests/ -v`
3. Check API docs: `http://localhost:8000/docs`
4. Review [API.md](API.md) for endpoint details
