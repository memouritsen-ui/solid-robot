# Research Tool API Documentation

Base URL: `http://localhost:8000`

## Overview

The Research Tool API provides REST endpoints for research operations and WebSocket endpoints for real-time communication.

## Authentication

Currently no authentication required (designed for local use).

---

## REST Endpoints

### Health Check

Check if the backend is running.

```
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

### Research Endpoints

#### Start Research

Begin a new research session.

```
POST /api/research/start
```

**Request Body:**
```json
{
  "query": "string (required, 3-500 chars)",
  "privacy_mode": "CLOUD_ALLOWED | LOCAL_ONLY | HYBRID",
  "domain": "medical | academic | competitive_intelligence | regulatory | null",
  "max_sources": 20
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | Research query (3-500 chars) |
| `privacy_mode` | string | No | `CLOUD_ALLOWED` | Privacy mode |
| `domain` | string | No | `null` | Domain hint for auto-config |
| `max_sources` | int | No | `20` | Max sources (1-100) |

**Response:**
```json
{
  "session_id": "uuid",
  "status": "started",
  "message": "Research workflow initiated"
}
```

---

#### Get Research Status

Check status of a research session.

```
GET /api/research/{session_id}/status
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | UUID from start response |

**Response:**
```json
{
  "session_id": "uuid",
  "status": "running | completed | failed | stopped",
  "current_phase": "clarify | plan | collect | process | analyze | evaluate | synthesize",
  "sources_queried": 15,
  "entities_found": 42,
  "facts_extracted": 87,
  "saturation_metrics": {
    "new_fact_rate": 0.12,
    "source_agreement": 0.85,
    "confidence": 0.78
  },
  "stop_reason": "string | null",
  "export_path": "string | null"
}
```

**Error Responses:**
| Code | Description |
|------|-------------|
| 404 | Session not found |

---

#### Approve Research Plan

Approve the research plan to continue workflow.

```
POST /api/research/{session_id}/approve
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session UUID |

**Response:**
```json
{
  "session_id": "uuid",
  "status": "approved",
  "message": "Research approved, continuing workflow"
}
```

**Error Responses:**
| Code | Description |
|------|-------------|
| 400 | Session not waiting for approval |
| 404 | Session not found |

---

#### Stop Research

Stop a running research session early.

```
POST /api/research/{session_id}/stop
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session UUID |

**Response:**
```json
{
  "session_id": "uuid",
  "status": "stopping",
  "message": "Stop signal sent to research workflow"
}
```

**Error Responses:**
| Code | Description |
|------|-------------|
| 400 | Session not running |
| 404 | Session not found |

---

#### Get Research Report

Get the final research report.

```
GET /api/research/{session_id}/report
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session UUID |

**Response:** Full research report (structure varies by domain)

**Error Responses:**
| Code | Description |
|------|-------------|
| 400 | Research not completed |
| 404 | Session or report not found |

---

### Export Endpoints

#### Get Export Formats

List available export formats.

```
GET /api/export/formats
```

**Response:**
```json
[
  {
    "format": "markdown",
    "mime_type": "text/markdown",
    "file_extension": "md",
    "description": "Markdown document for easy reading and editing"
  },
  {
    "format": "json",
    "mime_type": "application/json",
    "file_extension": "json",
    "description": "Structured JSON for programmatic access"
  },
  {
    "format": "pdf",
    "mime_type": "application/pdf",
    "file_extension": "pdf",
    "description": "PDF document for printing and sharing"
  },
  {
    "format": "docx",
    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "file_extension": "docx",
    "description": "Microsoft Word document"
  },
  {
    "format": "pptx",
    "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "file_extension": "pptx",
    "description": "Microsoft PowerPoint presentation"
  },
  {
    "format": "xlsx",
    "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "file_extension": "xlsx",
    "description": "Microsoft Excel spreadsheet"
  }
]
```

---

#### Export Research

Export research results to a specific format.

```
POST /api/export
```

**Request Body:**
```json
{
  "format": "markdown | json | pdf | docx | pptx | xlsx",
  "query": "Original research query",
  "domain": "medical",
  "summary": "Executive summary text",
  "facts": [
    {
      "statement": "Fact statement",
      "confidence": 0.85,
      "sources": ["source_id_1", "source_id_2"],
      "contradictions": []
    }
  ],
  "sources": [
    {
      "id": "source_id",
      "title": "Source title",
      "url": "https://example.com",
      "type": "academic | news | official | other",
      "reliability": 0.9
    }
  ],
  "confidence_score": 0.82,
  "limitations": [
    "Limited to English sources",
    "Data as of 2025"
  ],
  "metadata": {}
}
```

**Response:** Binary file download with appropriate Content-Disposition header.

**Error Responses:**
| Code | Description |
|------|-------------|
| 400 | Invalid format |
| 500 | Export failed |

---

### Performance Metrics

Get performance metrics for monitoring.

```
GET /api/metrics/performance
```

**Response:**
```json
{
  "slow_endpoints": [
    {
      "endpoint": "/api/research/start",
      "method": "POST",
      "avg_ms": 150.5
    }
  ],
  "health_stats": {
    "count": 100,
    "avg_ms": 2.3,
    "p95_ms": 5.0,
    "p99_ms": 10.0
  }
}
```

---

## WebSocket Endpoints

### Chat WebSocket

Real-time chat with streaming LLM responses.

```
ws://localhost:8000/ws/chat
```

**Client → Server Messages:**
```json
{
  "type": "message",
  "content": "User message text",
  "privacy_mode": "LOCAL_ONLY | CLOUD_ALLOWED | HYBRID"
}
```

**Server → Client Messages:**

Token streaming:
```json
{
  "type": "token",
  "content": "token_text"
}
```

Completion:
```json
{
  "type": "done",
  "model_used": "qwen2.5:32b-instruct",
  "reasoning": "Model selection reasoning"
}
```

Error:
```json
{
  "type": "error",
  "message": "Error description"
}
```

---

### Research Progress WebSocket

Real-time research progress updates.

```
ws://localhost:8000/ws/research/{session_id}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session UUID from /api/research/start |

**Server → Client Messages:**

Progress update:
```json
{
  "type": "progress",
  "phase": "collect",
  "message": "Querying Semantic Scholar...",
  "sources_queried": 5,
  "entities_found": 12,
  "facts_extracted": 28
}
```

Completion:
```json
{
  "type": "complete",
  "message": "Research complete",
  "sources_queried": 15,
  "entities_found": 42,
  "facts_extracted": 87,
  "data": {
    "summary": "...",
    "confidence": 0.82
  }
}
```

Error:
```json
{
  "type": "error",
  "message": "Error description"
}
```

---

## Privacy Modes

| Mode | Description | LLM Usage |
|------|-------------|-----------|
| `LOCAL_ONLY` | All processing on device | Ollama only |
| `CLOUD_ALLOWED` | Cloud LLM when beneficial | Ollama + Claude API |
| `HYBRID` | Local preferred, cloud fallback | Local first |

---

## Research Phases

| Phase | Description |
|-------|-------------|
| `clarify` | Query understanding and clarification |
| `plan` | Research plan generation |
| `collect` | Data collection from sources |
| `process` | Document processing and extraction |
| `analyze` | Entity and relationship analysis |
| `evaluate` | Saturation and quality evaluation |
| `synthesize` | Final report synthesis |

---

## Error Handling

All errors return JSON with this structure:
```json
{
  "detail": "Error message"
}
```

Common HTTP status codes:
| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid input) |
| 404 | Resource not found |
| 500 | Server error |

---

## Rate Limits

No rate limits for local use. Search providers have their own limits:
- Semantic Scholar: 1 request/second
- PubMed: 3 requests/second
- Others: Provider-specific

---

## Examples

### Python Example

```python
import httpx
import asyncio

async def run_research():
    async with httpx.AsyncClient() as client:
        # Start research
        response = await client.post(
            "http://localhost:8000/api/research/start",
            json={
                "query": "What are the latest treatments for Type 2 diabetes?",
                "privacy_mode": "LOCAL_ONLY",
                "domain": "medical"
            }
        )
        session_id = response.json()["session_id"]

        # Poll for status
        while True:
            status = await client.get(
                f"http://localhost:8000/api/research/{session_id}/status"
            )
            data = status.json()

            if data["status"] in ["completed", "failed"]:
                break

            await asyncio.sleep(2)

        # Get report
        report = await client.get(
            f"http://localhost:8000/api/research/{session_id}/report"
        )
        return report.json()

asyncio.run(run_research())
```

### WebSocket Example

```python
import asyncio
import websockets
import json

async def chat():
    async with websockets.connect("ws://localhost:8000/ws/chat") as ws:
        # Send message
        await ws.send(json.dumps({
            "type": "message",
            "content": "What is machine learning?",
            "privacy_mode": "LOCAL_ONLY"
        }))

        # Receive tokens
        response = ""
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "token":
                response += data["content"]
                print(data["content"], end="", flush=True)
            elif data["type"] == "done":
                print(f"\n\nModel: {data['model_used']}")
                break
            elif data["type"] == "error":
                print(f"Error: {data['message']}")
                break

asyncio.run(chat())
```

---

## OpenAPI Specification

FastAPI auto-generates OpenAPI docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
