# Research Tool

A professional-grade research assistant with privacy-first design, intelligent source selection, and comprehensive export capabilities.

## Features

- **Multi-Source Research**: Tavily, Exa, Semantic Scholar, PubMed, arXiv, Brave Search
- **Privacy Modes**: Local-only, hybrid, or cloud - you control where data goes
- **Domain Detection**: Automatically optimizes for medical, regulatory, academic, or competitive intelligence
- **LangGraph Agent**: Single ReAct agent with saturation detection and cross-verification
- **Multi-Format Export**: Markdown, JSON, PDF, DOCX, PPTX, XLSX
- **SwiftUI Interface**: Native macOS application

## Requirements

| Component | Version |
|-----------|---------|
| macOS | 14.0+ (Sonoma) |
| Python | 3.11+ |
| Xcode | 15+ |
| Ollama | Latest |
| uv | Latest |

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/memouritsen-ui/solid-robot.git
cd solid-robot
```

### 2. Install Backend Dependencies

```bash
cd backend
uv sync
uv sync --extra dev  # For development tools
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

**Minimum required**: `TAVILY_API_KEY`

For cloud models: Add `ANTHROPIC_API_KEY`

### 4. Setup Ollama (for local models)

```bash
# Install Ollama from https://ollama.ai
ollama pull qwen2.5:32b-instruct-q5_K_M  # Primary local model
ollama pull llama3.1:8b-instruct-q8_0    # Fast fallback
```

### 5. Install Playwright (for web crawling)

```bash
cd backend
uv run playwright install
```

### 6. Start Backend

```bash
cd backend
uv run uvicorn src.research_tool.main:app --host 127.0.0.1 --port 8000
```

### 7. Build GUI (optional)

Open `gui/ResearchTool/ResearchTool.xcodeproj` in Xcode and build.

## API Keys

| Service | Required | Purpose | Get Key |
|---------|----------|---------|---------|
| Tavily | Yes | Primary web search | [tavily.com](https://tavily.com) |
| Anthropic | No | Cloud LLM (Claude) | [console.anthropic.com](https://console.anthropic.com) |
| Exa | No | Enhanced search | [exa.ai](https://exa.ai) |
| Brave | No | Alternative search | [brave.com/search/api](https://brave.com/search/api) |
| Semantic Scholar | No | Academic search | [api.semanticscholar.org](https://api.semanticscholar.org) |

## Privacy Modes

| Mode | Description | Internet |
|------|-------------|----------|
| `LOCAL_ONLY` | All processing on device | No cloud LLM calls |
| `CLOUD_ALLOWED` | Cloud LLM when beneficial | Yes |
| `LOCAL_PREFERRED` | Local first, cloud fallback | Minimal |

## Project Structure

```
solid-robot/
├── backend/                    # Python FastAPI backend
│   ├── src/research_tool/      # Main package
│   │   ├── agent/              # LangGraph research agent
│   │   ├── api/                # REST + WebSocket endpoints
│   │   ├── core/               # Config, logging, exceptions
│   │   ├── models/             # Pydantic models
│   │   ├── services/           # LLM, memory, search services
│   │   └── utils/              # Retry, circuit breaker
│   ├── data/                   # Domain configs
│   ├── templates/              # Export templates
│   └── tests/                  # 650+ tests
├── gui/                        # SwiftUI macOS app
│   └── ResearchTool/
├── scripts/                    # Setup and run scripts
└── docs/                       # Documentation
```

## Running Tests

```bash
cd backend

# Run all tests
uv run python -m pytest tests/ -v

# Run with coverage
uv run python -m pytest tests/ --cov=src/research_tool --cov-report=html

# Run linting
uv run ruff check src/ tests/

# Run type checking
uv run python -m mypy src/ --ignore-missing-imports
```

## API Endpoints

### Health Check
```
GET /api/health
```

### Research
```
POST /api/research/start      # Start research task
GET /api/research/{id}/status # Check status
POST /api/research/{id}/stop  # Cancel research
```

### Export
```
POST /api/export              # Export results
GET /api/export/formats       # List available formats
```

### WebSocket
```
ws://localhost:8000/ws/chat        # Chat interface
ws://localhost:8000/ws/research    # Research progress
```

## Development

### Code Quality

```bash
# Pre-commit hooks
uv run pre-commit install

# Format check
uv run ruff check src/ tests/

# Type check
uv run python -m mypy src/ --ignore-missing-imports

# Security scan
uv run bandit -r src/
```

### Test Coverage Goals

- Overall: >90%
- Critical paths: 100%
- Edge cases: Comprehensive

## Architecture

```
┌─────────────────────────────────────────────────┐
│              SwiftUI GUI (macOS)                │
└────────────────────┬────────────────────────────┘
                     │ WebSocket + REST
┌────────────────────▼────────────────────────────┐
│           FastAPI Backend (Python)              │
├─────────────────────────────────────────────────┤
│  LiteLLM Router  │  LangGraph Agent  │  Memory  │
├─────────────────────────────────────────────────┤
│  Ollama (local)  │  Search APIs  │  LanceDB    │
└─────────────────────────────────────────────────┘
```

## License

Private repository. All rights reserved.

## Support

For issues, see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) or open an issue.
