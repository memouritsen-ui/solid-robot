# RESEARCH TOOL — META BUILD GUIDE v2.0
## Comprehensive Standalone Build Constitution

**Document Purpose**: This is the authoritative reference for all build decisions. Every architectural choice, every code commit, every feature implementation MUST be checked against this document. If something conflicts with this document, the build is wrong — not the document.

**Document Status**: LOCKED after user confirmation. Changes require explicit user approval.

**Self-Sufficiency**: This document contains ALL information needed to build the tool correctly, even if conversation context is lost. No external references required except official library documentation.

---

# PART 1: IMMUTABLE REQUIREMENTS

## 1.1 Core Success Criteria

The tool is successful when ALL of the following are true:

| # | Criterion | Verification Method |
|---|-----------|---------------------|
| 1 | User describes research task in plain language → tool understands and asks clarifying questions until clarity achieved | Manual testing with ambiguous queries |
| 2 | Executes at PROFESSIONAL SERVICE LEVEL — what a paid intelligence firm would deliver, not amateur or skilled individual | Benchmark against actual CI firm deliverables |
| 3 | Shows progress in plain language as it works — user never wonders "what's happening?" | Real-time GUI status updates visible |
| 4 | Uses memory INTELLIGENTLY to plan searches, pivot when hitting known territory, develop leads automatically, prevent fruitless searches | Memory retrieval logging + decision audit trail |
| 5 | Asks user for clarification ONLY when genuinely needed — not as escape hatch | Clarification request logging + justification |
| 6 | Exports in format suited to next step — keeps data accessible and structured | Export validation against downstream tools |
| 7 | RECOMMENDS intelligently whether local/cloud/hybrid is best for specific task — asks user to confirm | Recommendation logging with reasoning |
| 8 | Conversational interface feels like talking to Claude — natural, responsive, intelligent | User subjective assessment |

**NON-NEGOTIABLE**: All eight criteria must be satisfied. Partial success is failure.

## 1.2 User Rules for This Project

These rules govern the working relationship and decision-making process:

| Rule | Description | Enforcement |
|------|-------------|-------------|
| EXPLICIT CONFIRMATION | Nothing proceeds without user confirmation | All major decisions logged with user approval timestamp |
| USER DECIDES WHAT/WHY | User defines requirements and goals | Requirements traced to user statements |
| CLAUDE DECIDES HOW | Claude makes technical implementation decisions | Technical decisions documented with rationale |
| TIME NOT A CONSTRAINT | Take as long as needed to do it right | No shortcuts justified by time pressure |
| MONEY NOT A CONSTRAINT | Use best tools/services regardless of cost | Cost not a decision factor |
| TOKENS NOT A CONSTRAINT | Use as many API calls as needed | No premature optimization of API usage |
| ASK WHEN UNCLEAR | If something is ambiguous, ask — don't assume | Assumptions logged and flagged for review |
| HYPER-REALISTIC FEEDBACK | No sugarcoating, realistic timeframes, honest feasibility | All estimates include confidence intervals |
| PROFESSIONAL SERVICE OUTPUT | Every deliverable at professional quality | Quality checklist for every deliverable |
| CAN REBUILD IF NEEDED | Willing to tear down and start over if issues found | No sunk cost fallacy |

## 1.3 Operational Behavior Requirements

The tool MUST exhibit these behaviors:

### 1.3.1 Auto-Configuration
- Pre-loaded domain configurations for common research types (medical, regulatory, competitive intelligence, academic, news)
- Dynamic discovery for unfamiliar domains (research "how to research" first)
- **LEARNING**: Alters configurations in memory based on search results — what worked, what didn't, new sources discovered

### 1.3.2 Professional Research Methodology
- Follows OSINT intelligence cycle: Planning → Collection → Processing → Analysis → Dissemination
- Tiered investigation approach: Initial screening → Standard → Enhanced (automatic escalation based on indicators)
- Cross-verification of findings across multiple sources
- Source quality assessment and confidence scoring
- Explicit stopping criteria based on saturation metrics

### 1.3.3 Obstacle Handling
- Rate limits: Proxy rotation, request throttling, exponential backoff
- CAPTCHAs: Integration with solving services (2Captcha/Anti-Captcha), behavioral emulation
- Paywalls: Unpaywall API for legal open-access, preprint servers, author contact workflows
- JavaScript challenges: Headless browser with stealth plugins
- **CRITICAL**: When access is truly impossible, report WHY and add to memory — never fail silently

### 1.3.4 Intelligent Search Termination
- Informational saturation: <5% new information threshold
- Source saturation: Major source categories exhaustively covered
- Citation saturation: New sources reference already-collected sources
- User-defined limits when specified
- **ALWAYS** explain stopping rationale in plain language

### 1.3.5 Memory and Learning
- Remembers everything across projects
- Learns which sources are valuable for which domains
- Learns which search strategies work for which query types
- Learns user preferences and research patterns
- Uses memory to plan and optimize future searches

### 1.3.6 Privacy Mode
- Per-project choice: local-only OR cloud APIs
- Tool recommends optimal mode based on task analysis
- Asks user to confirm before executing
- Hybrid recommendations when appropriate (e.g., "use local for entity extraction, cloud for synthesis")

---

# PART 2: CONFIRMED TECHNICAL DECISIONS

## 2.1 Architecture Decisions

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Build approach | From scratch | GPT Researcher requires too much modification; clean architecture purpose-built for requirements |
| GUI framework | SwiftUI | User is Mac-only forever; best native experience; tightest system integration |
| Backend language | Python | AI ecosystem is Python-native; best library support |
| Backend-GUI connection | Local HTTP (FastAPI) | Standard practice for Swift-Python integration |
| Agent framework | LangGraph | State machine control, checkpointing, human-in-loop support |
| Agent pattern | Single ReAct agent with specialized tools | Multi-agent causes context fragmentation per Cognition Labs research |
| Model orchestration | LiteLLM | Unified API for 100+ providers, automatic fallback, cost tracking |
| Local inference | Ollama (NATIVE, never Docker) | Docker cannot access Metal GPU on macOS |
| Vector database | LanceDB | Embedded, Rust-based, hybrid search, <700MB for 100K docs |
| Structured storage | SQLite | Metadata, sessions, preferences, graph relationships |
| Graph operations | NetworkX | In-memory graph algorithms for relationship mapping |

## 2.2 Model Configuration

| Use Case | Model | Rationale |
|----------|-------|-----------|
| Complex reasoning (local) | Qwen2.5-32B-Instruct Q5_K_M | Best open model at runnable size; ~15-20 tok/s |
| Fast tasks (local) | Llama-3.1-8B Q8_0 | Quick responses for simple operations |
| Maximum capability (cloud) | Claude API | Best reasoning when privacy not required |
| Automatic selection | LiteLLM Router | Matches task complexity to appropriate model |

**Memory Allocation (48GB M4 Max)**:
- 22GB: Qwen2.5-32B
- 4GB: Llama-3.1-8B
- 4GB: Vector DB operations
- 3GB: Application/GUI
- 15GB: Headroom for spikes

## 2.3 Search Tools

| Tool | Purpose | Integration |
|------|---------|-------------|
| Tavily | Primary web search | API - $8/1K queries, 93.3% grounding accuracy |
| Exa | Neural semantic search | API |
| Brave Search | Fallback/independent index | API (Bing deprecates Aug 2025 — avoid Bing) |
| Semantic Scholar | Academic papers | API - 1 RPS limit |
| arXiv | Preprints (physics, CS, math) | API - unrestricted |
| PubMed | Biomedical literature | API |
| Unpaywall | Legal open-access finder | API |
| Crawl4AI | Self-hosted web scraping | Local deployment |
| Jina Reader | Simple page extraction | API |
| Playwright | JavaScript-heavy sites, fallback | Local with stealth plugins |

## 2.4 Export Formats

| Format | Library | Use Case |
|--------|---------|----------|
| Markdown | Native | Universal interchange, Google AI Studio |
| JSON (structured) | Native | API consumption, downstream agents |
| PDF | WeasyPrint + Jinja2 | Formal reports |
| Word (.docx) | python-docx | Editable documents |
| PowerPoint (.pptx) | python-pptx | Presentations |
| Excel (.xlsx) | openpyxl | Structured data, analysis |

**Template System**: Jinja2 with contextually adaptive templates — export format chosen based on stated next step.

---

# PART 3: EMBEDDED RESEARCH FINDINGS

## 3.1 LangGraph Technical Specifications

### 3.1.1 Core Concepts (From Official Documentation + Research)

**StateGraph**: The fundamental building block. Represents workflow as directed graph.

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# State must be TypedDict with Annotated fields for accumulation
class ResearchState(TypedDict):
    query: str
    search_results: Annotated[list, operator.add]  # Accumulates across nodes
    entities: Annotated[list, operator.add]
    current_phase: str
    saturation_score: float
    completed: bool
```

**Nodes**: Functions that transform state. Each node receives state, returns partial state update.

```python
async def search_node(state: ResearchState) -> dict:
    results = await search_tool.search(state["query"])
    return {"search_results": results}  # Merged into state
```

**Edges**: Define transitions. Can be conditional.

```python
def should_continue(state: ResearchState) -> str:
    if state["saturation_score"] > 0.95:
        return "synthesize"
    if state["completed"]:
        return END
    return "search"  # Continue searching

graph.add_conditional_edges(
    "evaluate",
    should_continue,
    {
        "search": "search_node",
        "synthesize": "synthesis_node",
        END: END
    }
)
```

**Checkpointing**: Built-in persistence for resumption.

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("research_checkpoints.db")
app = graph.compile(checkpointer=checkpointer)

# Resume from checkpoint
config = {"configurable": {"thread_id": "research-123"}}
result = await app.ainvoke(state, config)
```

### 3.1.2 Human-in-the-Loop Pattern

```python
from langgraph.graph import StateGraph
from langgraph.types import interrupt

async def get_user_approval(state: ResearchState) -> dict:
    # This causes the graph to pause and return control
    user_input = interrupt({
        "question": "Approve this research plan?",
        "plan": state["research_plan"]
    })
    return {"user_approved": user_input["approved"]}
```

### 3.1.3 Parallel Execution (Send API)

```python
from langgraph.constants import Send

def dispatch_searches(state: ResearchState) -> list[Send]:
    # Execute multiple searches in parallel
    return [
        Send("search_source", {"source": "tavily", "query": state["query"]}),
        Send("search_source", {"source": "exa", "query": state["query"]}),
        Send("search_source", {"source": "semantic_scholar", "query": state["query"]})
    ]
```

## 3.2 Ollama Configuration for M4 Max

### 3.2.1 Environment Variables (MUST SET)

```bash
# ~/.zshrc or launch configuration
export OLLAMA_NUM_PARALLEL=4        # Concurrent requests
export OLLAMA_FLASH_ATTENTION=1     # Enable Flash Attention for speed
export OLLAMA_KEEP_ALIVE=5m         # Keep model loaded 5 minutes
export OLLAMA_MAX_LOADED_MODELS=2   # Qwen + Llama simultaneously
```

### 3.2.2 Metal GPU Memory Limit

Default limit is 75% of unified memory (~36GB on 48GB machine). To raise:

```bash
sudo sysctl iogpu.wired_limit_mb=40960  # Allow ~40GB
```

**WARNING**: This requires sudo. Document for user to run manually.

### 3.2.3 Model Pull Commands

```bash
ollama pull qwen2.5:32b-instruct-q5_K_M
ollama pull llama3.1:8b-instruct-q8_0
```

### 3.2.4 Expected Performance Benchmarks

| Model | Tokens/sec | First Token Latency | Memory Usage |
|-------|------------|---------------------|--------------|
| Qwen2.5-32B Q5_K_M | 15-20 | 1.5-2.5s | ~22GB |
| Llama-3.1-8B Q8_0 | 45-60 | 0.3-0.5s | ~4GB |

**CRITICAL**: If performance is significantly below these numbers, check:
1. Ollama running natively (not in Docker)
2. OLLAMA_FLASH_ATTENTION=1 set
3. No other GPU-intensive processes running

## 3.3 LiteLLM Router Configuration

### 3.3.1 Basic Setup

```python
from litellm import Router

router = Router(
    model_list=[
        {
            "model_name": "local-fast",
            "litellm_params": {
                "model": "ollama/llama3.1:8b-instruct-q8_0",
                "api_base": "http://localhost:11434"
            }
        },
        {
            "model_name": "local-powerful",
            "litellm_params": {
                "model": "ollama/qwen2.5:32b-instruct-q5_K_M",
                "api_base": "http://localhost:11434"
            }
        },
        {
            "model_name": "cloud-best",
            "litellm_params": {
                "model": "claude-3-5-sonnet-20241022",
                "api_key": "os.environ/ANTHROPIC_API_KEY"
            }
        }
    ],
    fallbacks=[
        {"local-powerful": ["cloud-best"]},  # If local fails, use cloud
        {"cloud-best": ["local-powerful"]}   # If cloud fails, use local
    ],
    set_verbose=True
)
```

### 3.3.2 Model Selection Logic

```python
def select_model(task_complexity: str, privacy_required: bool) -> str:
    if privacy_required:
        # Only local models
        if task_complexity == "high":
            return "local-powerful"
        return "local-fast"
    else:
        # Can use cloud
        if task_complexity == "high":
            return "cloud-best"
        elif task_complexity == "medium":
            return "local-powerful"
        return "local-fast"
```

### 3.3.3 Cost Tracking

```python
from litellm import completion

response = completion(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello"}]
)

# Access cost information
cost = response._hidden_params.get("response_cost", 0)
```

## 3.4 LanceDB Configuration

### 3.4.1 Setup and Schema

```python
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry

# Use local embedding model for privacy
embedder = get_registry().get("sentence-transformers").create(
    name="BAAI/bge-small-en-v1.5"
)

class ResearchDocument(LanceModel):
    text: str = embedder.SourceField()
    vector: Vector(384) = embedder.VectorField()  # bge-small dimension
    source_url: str
    source_name: str
    retrieved_at: str
    confidence_score: float
    research_id: str
    domain: str

db = lancedb.connect("./research_memory")
table = db.create_table("documents", schema=ResearchDocument, mode="overwrite")
```

### 3.4.2 Hybrid Search (60% Semantic + 40% Keyword)

```python
from lancedb.rerankers import CrossEncoderReranker

reranker = CrossEncoderReranker(model_name="BAAI/bge-reranker-v2-m3")

results = table.search(
    query="drone regulations Europe",
    query_type="hybrid"  # Combines vector + FTS
).rerank(reranker).limit(20).to_list()
```

### 3.4.3 Chunking Strategy

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,      # ~400-512 tokens
    chunk_overlap=64,    # ~10-15% overlap
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = splitter.split_text(document_text)
```

**Research Finding**: 400-512 token chunks with 10-20% overlap achieve 88-89% recall in retrieval benchmarks.

## 3.5 Search Tool Configurations

### 3.5.1 Tavily

```python
from tavily import TavilyClient

client = TavilyClient(api_key="...")

response = client.search(
    query="drone regulations EU 2024",
    search_depth="advanced",  # More thorough
    include_answer=True,      # Get synthesized answer
    include_raw_content=True, # Full page content
    max_results=10
)
```

**Rate Limits**: 1000 requests/month on free tier, unlimited on paid.

### 3.5.2 Semantic Scholar

```python
import httpx

async def search_semantic_scholar(query: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": 100,
                "fields": "title,abstract,authors,year,citationCount,url"
            },
            headers={"x-api-key": "..."}  # Optional, increases limits
        )
        return response.json()["data"]
```

**CRITICAL RATE LIMIT**: 1 request per second without API key. Implement explicit rate limiting:

```python
import asyncio

class RateLimiter:
    def __init__(self, requests_per_second: float):
        self.delay = 1.0 / requests_per_second
        self.last_request = 0
    
    async def acquire(self):
        now = asyncio.get_event_loop().time()
        wait_time = self.last_request + self.delay - now
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        self.last_request = asyncio.get_event_loop().time()

semantic_scholar_limiter = RateLimiter(1.0)  # 1 RPS
```

### 3.5.3 Unpaywall (Legal Open Access)

```python
async def find_open_access(doi: str) -> Optional[str]:
    """Returns URL to legal open-access version if available."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.unpaywall.org/v2/{doi}",
            params={"email": "your-email@example.com"}  # Required
        )
        data = response.json()
        
        if data.get("is_oa"):
            best_location = data.get("best_oa_location", {})
            return best_location.get("url_for_pdf") or best_location.get("url")
        return None
```

### 3.5.4 Playwright with Stealth

```python
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def scrape_with_stealth(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ..."
        )
        page = await context.new_page()
        
        # Apply stealth to avoid detection
        await stealth_async(page)
        
        await page.goto(url, wait_until="networkidle")
        content = await page.content()
        
        await browser.close()
        return content
```

## 3.6 Obstacle Handling Technical Details

### 3.6.1 Exponential Backoff Implementation

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((RateLimitError, TimeoutError))
)
async def fetch_with_backoff(url: str) -> str:
    # Attempts: immediate, 4s, 8s, 16s, 32s (capped at 60s)
    ...
```

### 3.6.2 CAPTCHA Service Integration (2Captcha)

```python
import httpx

async def solve_captcha(site_key: str, page_url: str) -> str:
    """Solve reCAPTCHA v2 using 2Captcha service."""
    api_key = os.environ["TWOCAPTCHA_API_KEY"]
    
    # Submit CAPTCHA
    async with httpx.AsyncClient() as client:
        submit = await client.post(
            "http://2captcha.com/in.php",
            data={
                "key": api_key,
                "method": "userrecaptcha",
                "googlekey": site_key,
                "pageurl": page_url,
                "json": 1
            }
        )
        request_id = submit.json()["request"]
        
        # Poll for solution (typically 20-60 seconds)
        for _ in range(30):
            await asyncio.sleep(5)
            result = await client.get(
                "http://2captcha.com/res.php",
                params={"key": api_key, "action": "get", "id": request_id, "json": 1}
            )
            data = result.json()
            if data["status"] == 1:
                return data["request"]  # The solution token
        
        raise CaptchaError("CAPTCHA solving timeout")
```

### 3.6.3 Proxy Rotation

```python
class ProxyRotator:
    def __init__(self, proxies: list[str]):
        self.proxies = proxies
        self.index = 0
        self.failed = set()
    
    def get_next(self) -> Optional[str]:
        available = [p for p in self.proxies if p not in self.failed]
        if not available:
            return None
        proxy = available[self.index % len(available)]
        self.index += 1
        return proxy
    
    def mark_failed(self, proxy: str):
        self.failed.add(proxy)
```

## 3.7 Saturation Detection Implementation

### 3.7.1 Metrics Calculation

```python
from dataclasses import dataclass

@dataclass
class SaturationMetrics:
    new_entities_ratio: float      # New entities / total entities
    new_facts_ratio: float         # New facts / total facts
    citation_circularity: float    # % of sources citing known sources
    source_coverage: float         # % of mapped sources queried

def calculate_saturation(
    current_entities: set,
    previous_entities: set,
    current_facts: set,
    previous_facts: set,
    citation_graph: dict,
    source_checklist: dict
) -> SaturationMetrics:
    
    new_entities = current_entities - previous_entities
    new_facts = current_facts - previous_facts
    
    new_entities_ratio = len(new_entities) / max(len(current_entities), 1)
    new_facts_ratio = len(new_facts) / max(len(current_facts), 1)
    
    # Citation circularity: what % of new sources cite existing sources
    circular_citations = 0
    for source, citations in citation_graph.items():
        if source in new_entities:
            if any(c in previous_entities for c in citations):
                circular_citations += 1
    citation_circularity = circular_citations / max(len(new_entities), 1)
    
    # Source coverage
    completed = sum(1 for v in source_checklist.values() if v)
    source_coverage = completed / len(source_checklist)
    
    return SaturationMetrics(
        new_entities_ratio=new_entities_ratio,
        new_facts_ratio=new_facts_ratio,
        citation_circularity=citation_circularity,
        source_coverage=source_coverage
    )

def should_stop(metrics: SaturationMetrics) -> tuple[bool, str]:
    """Returns (should_stop, reason)."""
    
    if metrics.new_entities_ratio < 0.05 and metrics.new_facts_ratio < 0.05:
        return True, "Informational saturation: <5% new information in last cycle"
    
    if metrics.source_coverage > 0.95:
        return True, "Source exhaustion: >95% of mapped sources queried"
    
    if metrics.citation_circularity > 0.80:
        return True, "Citation circularity: >80% of new sources reference existing findings"
    
    return False, ""
```

---

# PART 4: CODE SKELETONS

## 4.1 Core Data Structures

### 4.1.1 Research State

```python
from typing import TypedDict, Annotated, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import operator

class ResearchPhase(Enum):
    PLANNING = "planning"
    COLLECTION = "collection"
    PROCESSING = "processing"
    ANALYSIS = "analysis"
    DISSEMINATION = "dissemination"

class PrivacyMode(Enum):
    LOCAL_ONLY = "local_only"
    CLOUD_ALLOWED = "cloud_allowed"
    HYBRID = "hybrid"

@dataclass
class SourceResult:
    source_name: str
    source_url: str
    content: str
    retrieved_at: datetime
    access_method: str  # "api", "scrape", "cached"
    confidence: float
    raw_response: Optional[dict] = None

@dataclass
class Entity:
    name: str
    entity_type: str  # "company", "person", "regulation", "product", etc.
    attributes: dict
    sources: list[str]  # URLs where found
    confidence: float

@dataclass
class Fact:
    statement: str
    sources: list[str]
    verification_status: str  # "single_source", "cross_verified", "conflicting"
    confidence: float
    contradictions: list[str] = field(default_factory=list)

class ResearchState(TypedDict):
    # Identifiers
    research_id: str
    created_at: str
    
    # User input
    original_query: str
    clarified_query: str
    user_constraints: dict
    
    # Configuration
    domain: str
    privacy_mode: PrivacyMode
    source_strategy: dict
    
    # Phase tracking
    current_phase: ResearchPhase
    completed_phases: list[str]
    
    # Collected data (Annotated for accumulation)
    source_results: Annotated[list[SourceResult], operator.add]
    entities: Annotated[list[Entity], operator.add]
    facts: Annotated[list[Fact], operator.add]
    
    # Obstacles encountered
    access_failures: Annotated[list[dict], operator.add]
    
    # Saturation tracking
    saturation_history: list[SaturationMetrics]
    
    # Output
    final_report: Optional[str]
    export_path: Optional[str]
    
    # Audit
    decision_log: Annotated[list[dict], operator.add]
```

### 4.1.2 Domain Configuration

```python
@dataclass
class SourceConfig:
    name: str
    priority: int  # 1 = highest
    source_type: str  # "api", "scrape", "database"
    rate_limit: Optional[float]  # requests per second
    requires_auth: bool
    auth_env_var: Optional[str]

@dataclass
class DomainConfiguration:
    domain_name: str
    description: str
    primary_sources: list[SourceConfig]
    secondary_sources: list[SourceConfig]
    fallback_sources: list[SourceConfig]
    entity_types: list[str]
    typical_query_patterns: list[str]
    quality_indicators: list[str]
    effectiveness_score: float = 0.5  # Updated by learning
    last_updated: Optional[datetime] = None

# Pre-loaded configurations
DOMAIN_CONFIGS = {
    "medical": DomainConfiguration(
        domain_name="medical",
        description="Medical and biomedical research",
        primary_sources=[
            SourceConfig("pubmed", 1, "api", 3.0, False, None),
            SourceConfig("semantic_scholar", 2, "api", 1.0, False, None),
        ],
        secondary_sources=[
            SourceConfig("unpaywall", 1, "api", 10.0, False, None),
            SourceConfig("biorxiv", 2, "api", None, False, None),
        ],
        fallback_sources=[
            SourceConfig("tavily", 1, "api", None, True, "TAVILY_API_KEY"),
        ],
        entity_types=["drug", "disease", "gene", "protein", "clinical_trial"],
        typical_query_patterns=["treatment for X", "mechanism of X", "clinical trials X"],
        quality_indicators=["peer_reviewed", "citation_count", "journal_impact"],
    ),
    "competitive_intelligence": DomainConfiguration(
        domain_name="competitive_intelligence",
        description="Company and market intelligence",
        primary_sources=[
            SourceConfig("tavily", 1, "api", None, True, "TAVILY_API_KEY"),
            SourceConfig("exa", 2, "api", None, True, "EXA_API_KEY"),
        ],
        secondary_sources=[
            SourceConfig("brave", 1, "api", None, True, "BRAVE_API_KEY"),
        ],
        fallback_sources=[
            SourceConfig("playwright_scrape", 1, "scrape", 0.5, False, None),
        ],
        entity_types=["company", "person", "product", "funding_round", "partnership"],
        typical_query_patterns=["competitors of X", "market size X", "funding X"],
        quality_indicators=["recency", "source_authority", "data_specificity"],
    ),
    # ... more domains
}
```

### 4.1.3 Memory Schema

```python
# SQLite Schema
SQLITE_SCHEMA = """
-- Research sessions
CREATE TABLE IF NOT EXISTS research_sessions (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    domain TEXT,
    privacy_mode TEXT,
    started_at TEXT,
    completed_at TEXT,
    status TEXT,
    result_summary TEXT
);

-- Source effectiveness tracking
CREATE TABLE IF NOT EXISTS source_effectiveness (
    source_name TEXT PRIMARY KEY,
    domain TEXT,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_relevance_score REAL DEFAULT 0.5,
    last_used TEXT,
    UNIQUE(source_name, domain)
);

-- Access failures (for learning what to avoid)
CREATE TABLE IF NOT EXISTS access_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT,
    source_name TEXT,
    failure_type TEXT,
    failure_reason TEXT,
    occurred_at TEXT,
    permanent BOOLEAN DEFAULT FALSE
);

-- Domain configurations (learned modifications)
CREATE TABLE IF NOT EXISTS domain_config_overrides (
    domain TEXT PRIMARY KEY,
    config_json TEXT,
    learned_at TEXT
);

-- User preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT
);
"""
```

## 4.2 Interface Definitions

### 4.2.1 Search Provider Interface

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator

class SearchProvider(ABC):
    """Abstract interface for all search sources."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this source."""
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> str:
        """Type: 'api', 'scrape', 'database'."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        **kwargs
    ) -> list[SourceResult]:
        """Execute search and return results."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Verify source is accessible."""
        pass
    
    @abstractmethod
    def get_rate_limit(self) -> Optional[float]:
        """Return requests per second limit, or None if unlimited."""
        pass


class TavilySearchProvider(SearchProvider):
    """Implementation for Tavily."""
    
    @property
    def name(self) -> str:
        return "tavily"
    
    @property
    def source_type(self) -> str:
        return "api"
    
    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SourceResult]:
        # Implementation
        ...
    
    async def health_check(self) -> bool:
        # Implementation
        ...
    
    def get_rate_limit(self) -> Optional[float]:
        return None  # No strict limit
```

### 4.2.2 Memory Repository Interface

```python
class MemoryRepository(ABC):
    """Abstract interface for memory storage."""
    
    @abstractmethod
    async def store_document(self, doc: ResearchDocument) -> str:
        """Store document, return ID."""
        pass
    
    @abstractmethod
    async def search_similar(
        self,
        query: str,
        limit: int = 10,
        domain_filter: Optional[str] = None
    ) -> list[ResearchDocument]:
        """Find similar documents."""
        pass
    
    @abstractmethod
    async def get_source_effectiveness(
        self,
        source_name: str,
        domain: str
    ) -> float:
        """Get learned effectiveness score for source in domain."""
        pass
    
    @abstractmethod
    async def update_source_effectiveness(
        self,
        source_name: str,
        domain: str,
        success: bool,
        relevance_score: float
    ) -> None:
        """Update source effectiveness based on result."""
        pass
    
    @abstractmethod
    async def record_access_failure(
        self,
        url: str,
        source_name: str,
        failure_type: str,
        failure_reason: str,
        permanent: bool = False
    ) -> None:
        """Record an access failure for learning."""
        pass
    
    @abstractmethod
    async def is_known_failure(self, url: str) -> bool:
        """Check if URL has permanent access failure."""
        pass
```

### 4.2.3 Model Provider Interface

```python
class ModelProvider(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> Union[str, AsyncIterator[str]]:
        """Generate completion."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if model is loaded/accessible."""
        pass
    
    @abstractmethod
    def get_context_window(self) -> int:
        """Return max context length."""
        pass
    
    @abstractmethod
    def requires_privacy(self) -> bool:
        """True if this is a local model."""
        pass
```

## 4.3 LangGraph Workflow Skeleton

```python
from langgraph.graph import StateGraph, END

def build_research_graph() -> StateGraph:
    """Construct the research workflow graph."""
    
    graph = StateGraph(ResearchState)
    
    # Add nodes
    graph.add_node("clarify", clarify_query_node)
    graph.add_node("plan", create_plan_node)
    graph.add_node("get_approval", get_user_approval_node)
    graph.add_node("collect", collection_node)
    graph.add_node("process", processing_node)
    graph.add_node("analyze", analysis_node)
    graph.add_node("evaluate", evaluate_saturation_node)
    graph.add_node("synthesize", synthesis_node)
    graph.add_node("export", export_node)
    
    # Define edges
    graph.add_edge("clarify", "plan")
    graph.add_edge("plan", "get_approval")
    graph.add_conditional_edges(
        "get_approval",
        lambda s: "collect" if s.get("user_approved") else "plan",
        {"collect": "collect", "plan": "plan"}
    )
    graph.add_edge("collect", "process")
    graph.add_edge("process", "analyze")
    graph.add_edge("analyze", "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        should_continue_research,
        {
            "continue": "collect",
            "synthesize": "synthesize"
        }
    )
    graph.add_edge("synthesize", "export")
    graph.add_edge("export", END)
    
    # Set entry point
    graph.set_entry_point("clarify")
    
    return graph


async def clarify_query_node(state: ResearchState) -> dict:
    """
    ═══════════════════════════════════════════════════════════════
    VERIFICATION CHECKPOINT: Before implementing this node, re-read:
    - Section 1.1 Criterion #1 (understanding user query)
    - Section 1.1 Criterion #5 (ask only when genuinely needed)
    - Section 5.4 Anti-Pattern #1 (asking unnecessary questions)
    ═══════════════════════════════════════════════════════════════
    """
    # Implementation
    ...


async def should_continue_research(state: ResearchState) -> str:
    """
    ═══════════════════════════════════════════════════════════════
    VERIFICATION CHECKPOINT: Before implementing this function, re-read:
    - Section 1.3.4 (Intelligent Search Termination)
    - Section 3.7 (Saturation Detection Implementation)
    - Section 5.4 Anti-Pattern #3 (stopping too early)
    - Section 5.4 Anti-Pattern #4 (stopping too late)
    ═══════════════════════════════════════════════════════════════
    """
    metrics = state["saturation_history"][-1] if state["saturation_history"] else None
    
    if metrics:
        should_stop, reason = should_stop(metrics)
        if should_stop:
            # Log the decision
            return "synthesize"
    
    return "continue"
```

## 4.4 SwiftUI-Python Communication

### 4.4.1 FastAPI Backend Endpoints

```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # SwiftUI app
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    query: str
    privacy_mode: str = "recommend"
    constraints: dict = {}

class MessageRequest(BaseModel):
    message: str
    research_id: Optional[str] = None

@app.post("/api/research/start")
async def start_research(request: ResearchRequest):
    """Start a new research task."""
    research_id = str(uuid.uuid4())
    # Queue research task
    return {"research_id": research_id, "status": "started"}

@app.get("/api/research/{research_id}/status")
async def get_status(research_id: str):
    """Get current research status."""
    ...

@app.websocket("/ws/research/{research_id}")
async def research_websocket(websocket: WebSocket, research_id: str):
    """Stream progress updates to GUI."""
    await websocket.accept()
    
    async for event in research_event_stream(research_id):
        await websocket.send_json({
            "type": event.type.value,
            "message": event.message,
            "details": event.details,
            "timestamp": event.timestamp.isoformat()
        })

@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """Conversational interface."""
    await websocket.accept()
    
    while True:
        data = await websocket.receive_json()
        
        async for token in stream_response(data["message"]):
            await websocket.send_json({
                "type": "token",
                "content": token
            })
        
        await websocket.send_json({"type": "done"})
```

### 4.4.2 SwiftUI WebSocket Client

```swift
import Foundation

class ResearchClient: ObservableObject {
    @Published var messages: [Message] = []
    @Published var currentStatus: String = ""
    @Published var isConnected: Bool = false
    
    private var webSocket: URLSessionWebSocketTask?
    private let baseURL = "http://localhost:8000"
    
    func connect() {
        let url = URL(string: "ws://localhost:8000/ws/chat")!
        webSocket = URLSession.shared.webSocketTask(with: url)
        webSocket?.resume()
        isConnected = true
        receiveMessage()
    }
    
    func sendMessage(_ text: String) {
        let message = ["message": text]
        guard let data = try? JSONEncoder().encode(message) else { return }
        
        webSocket?.send(.string(String(data: data, encoding: .utf8)!)) { error in
            if let error = error {
                print("Send error: \(error)")
            }
        }
    }
    
    private func receiveMessage() {
        webSocket?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    self?.handleMessage(text)
                default:
                    break
                }
                self?.receiveMessage()  // Continue listening
            case .failure(let error):
                print("Receive error: \(error)")
                self?.isConnected = false
            }
        }
    }
    
    private func handleMessage(_ text: String) {
        guard let data = text.data(using: .utf8),
              let json = try? JSONDecoder().decode(WSMessage.self, from: data) else {
            return
        }
        
        DispatchQueue.main.async {
            switch json.type {
            case "token":
                // Append to current message
                self.appendToken(json.content ?? "")
            case "done":
                // Message complete
                self.finalizeMessage()
            case "status":
                self.currentStatus = json.content ?? ""
            default:
                break
            }
        }
    }
}
```

---

# PART 5: ANTI-PATTERNS

## 5.1 Query Understanding Anti-Patterns

### Anti-Pattern #1: Asking Unnecessary Clarifying Questions

**WRONG**:
```
User: "Find information about drone regulations in Europe"
Agent: "What specific countries? What type of drones? Commercial or recreational? What time period?"
```

**RIGHT**:
```
User: "Find information about drone regulations in Europe"
Agent: [Starts research with broad EU scope, progressively narrows based on findings]
Agent: [Only asks if hits genuine ambiguity that blocks progress]
```

**Rule**: If you can make reasonable progress with a reasonable interpretation, DO SO. Ask only when stuck.

### Anti-Pattern #2: Treating Clarification as Escape Hatch

**WRONG**:
```
Agent: [Encounters difficulty]
Agent: "I need more information from you before I can proceed..."
```

**RIGHT**:
```
Agent: [Encounters difficulty]
Agent: [Tries alternative approaches]
Agent: [Only asks user if all approaches exhausted]
```

**Rule**: Clarification requests must be logged with justification. If pattern shows excessive requests, system is broken.

## 5.2 Search Strategy Anti-Patterns

### Anti-Pattern #3: Stopping Too Early

**WRONG**:
```
Agent: [Gets 10 results from first source]
Agent: "I found some information about your topic..."
```

**RIGHT**:
```
Agent: [Gets results from first source]
Agent: [Checks saturation metrics - still <5% threshold not met]
Agent: [Continues with additional sources until saturation]
```

**Rule**: Never stop on first results. Always check saturation metrics.

### Anti-Pattern #4: Stopping Too Late (Wasting Resources)

**WRONG**:
```
Agent: [Has 500 results, saturation at 98%]
Agent: [Continues querying more sources "to be thorough"]
```

**RIGHT**:
```
Agent: [Has results, saturation at 98%]
Agent: "Stopping search: 98% saturation reached, additional queries unlikely to yield new information"
```

**Rule**: When saturation threshold met, STOP. Explain why.

### Anti-Pattern #5: Ignoring Source Quality Scores

**WRONG**:
```
Agent: [Memory shows Source X has 0.2 effectiveness for this domain]
Agent: [Queries Source X first anyway]
```

**RIGHT**:
```
Agent: [Memory shows Source X has 0.2 effectiveness for this domain]
Agent: [Deprioritizes Source X, starts with higher-scored sources]
Agent: [Only uses Source X as fallback if primary sources insufficient]
```

**Rule**: Always check and use source effectiveness scores from memory.

## 5.3 Obstacle Handling Anti-Patterns

### Anti-Pattern #6: Silent Failure

**WRONG**:
```python
try:
    result = await fetch(url)
except Exception:
    pass  # Silently continue
```

**RIGHT**:
```python
try:
    result = await fetch(url)
except RateLimitError as e:
    await self.memory.record_access_failure(url, source, "rate_limit", str(e))
    self.emit_progress(f"Rate limited by {source}, backing off...")
    await asyncio.sleep(e.retry_after)
    # Retry or move to next source
except AccessDeniedError as e:
    await self.memory.record_access_failure(url, source, "access_denied", str(e), permanent=True)
    self.emit_progress(f"Cannot access {url}: {e.reason}")
    # Continue with other sources
```

**Rule**: Every failure must be logged, reported to user, and recorded in memory.

### Anti-Pattern #7: Infinite Retry Loops

**WRONG**:
```python
while True:
    try:
        result = await fetch(url)
        break
    except Exception:
        await asyncio.sleep(1)
```

**RIGHT**:
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=60))
async def fetch_with_retry(url: str) -> str:
    ...

try:
    result = await fetch_with_retry(url)
except RetryError:
    # All retries exhausted, record and move on
    await self.memory.record_access_failure(...)
```

**Rule**: Always have maximum retry limits. Fail gracefully after exhaustion.

## 5.4 Memory Anti-Patterns

### Anti-Pattern #8: Not Using Memory for Planning

**WRONG**:
```python
async def plan_research(query: str) -> ResearchPlan:
    # Start fresh every time
    domain = detect_domain(query)
    sources = DEFAULT_SOURCES[domain]
    ...
```

**RIGHT**:
```python
async def plan_research(query: str) -> ResearchPlan:
    domain = detect_domain(query)
    
    # Check memory for similar past research
    similar = await self.memory.search_similar(query, limit=5)
    if similar:
        # Learn from what worked before
        effective_sources = extract_effective_sources(similar)
        failed_urls = extract_failed_urls(similar)
    
    # Get learned source scores
    source_scores = await self.memory.get_source_effectiveness_all(domain)
    
    # Build plan using learned information
    ...
```

**Rule**: Always consult memory before planning. Learning is useless if not applied.

### Anti-Pattern #9: Not Updating Memory After Research

**WRONG**:
```python
async def complete_research(state: ResearchState):
    report = generate_report(state)
    return report  # Done, forget everything learned
```

**RIGHT**:
```python
async def complete_research(state: ResearchState):
    report = generate_report(state)
    
    # Update source effectiveness scores
    for source, results in state.results_by_source.items():
        await self.memory.update_source_effectiveness(
            source,
            state.domain,
            success=len(results) > 0,
            relevance_score=calculate_relevance(results)
        )
    
    # Store valuable entities for future reference
    for entity in state.entities:
        if entity.confidence > 0.8:
            await self.memory.store_entity(entity)
    
    # Update domain configuration if new sources discovered
    await self.update_domain_config(state)
    
    return report
```

**Rule**: Every research task must update memory. This is how the system learns.

## 5.5 Model Selection Anti-Patterns

### Anti-Pattern #10: Ignoring Privacy Mode

**WRONG**:
```python
# User selected local_only privacy mode
response = await router.complete(
    model="cloud-best",  # Sends data to cloud anyway
    messages=messages
)
```

**RIGHT**:
```python
def get_allowed_models(privacy_mode: PrivacyMode) -> list[str]:
    if privacy_mode == PrivacyMode.LOCAL_ONLY:
        return ["local-fast", "local-powerful"]
    elif privacy_mode == PrivacyMode.CLOUD_ALLOWED:
        return ["local-fast", "local-powerful", "cloud-best"]
    else:  # HYBRID
        # Specific rules for what goes where
        return [...]

# Always check privacy mode
allowed = get_allowed_models(state.privacy_mode)
model = select_best_available(allowed, task_complexity)
```

**Rule**: Privacy mode is a hard constraint. Never violate it.

## 5.6 Output Anti-Patterns

### Anti-Pattern #11: Omitting What Wasn't Found

**WRONG**:
```
Report: Here's what I found about drone regulations in Europe...
[Lists findings]
```

**RIGHT**:
```
Report: Here's what I found about drone regulations in Europe...
[Lists findings]

Limitations and Gaps:
- Could not access [specific sources] due to [reasons]
- No information found on [specific sub-topics]
- [X] sources were behind paywalls with no open-access versions
- Confidence is lower for [specific findings] due to single-source verification
```

**Rule**: Always report what you couldn't find and why. This is professional practice.

### Anti-Pattern #12: Not Explaining Stopping Rationale

**WRONG**:
```
Agent: Research complete. Here's your report.
```

**RIGHT**:
```
Agent: Research complete. Stopped because: informational saturation reached (only 2% new information in last 3 search cycles). Queried 47 sources across 5 categories. Here's your report.
```

**Rule**: Always explain WHY you stopped in plain language.

---

# PART 6: VERIFICATION CHECKPOINTS

## 6.1 Pre-Implementation Checkpoints

Before writing ANY code for a component, complete this checklist:

```
□ I have re-read the relevant sections of this META guide
□ I have identified which Success Criteria this component serves
□ I have identified which Anti-Patterns could apply
□ I have written the test cases BEFORE implementation
□ I have defined the interface/contract this component must satisfy
□ I have identified dependencies and verified they exist
```

## 6.2 Component-Specific Checkpoints

### Checkpoint: Query Clarification

```
BEFORE implementing clarification logic, verify:
□ Re-read Section 1.1 Criterion #1 and #5
□ Re-read Section 5.1 Anti-Patterns #1 and #2
□ Implement logging of all clarification requests with justification
□ Test: ambiguous query should proceed with reasonable interpretation
□ Test: genuinely blocking ambiguity should ask ONE focused question
```

### Checkpoint: Search Execution

```
BEFORE implementing search logic, verify:
□ Re-read Section 3.5 (Search Tool Configurations)
□ Re-read Section 5.2 Anti-Patterns #3, #4, #5
□ Implement rate limiting per Section 3.5.2
□ Implement circuit breaker per Section 4.3.1
□ Test: rate limit hit should backoff and retry
□ Test: source failure should try fallback
□ Test: all sources failed should report clearly
```

### Checkpoint: Saturation Detection

```
BEFORE implementing stopping logic, verify:
□ Re-read Section 1.3.4 (Intelligent Search Termination)
□ Re-read Section 3.7 (Saturation Detection Implementation)
□ Re-read Section 5.2 Anti-Patterns #3 and #4
□ Use exact thresholds from Section 3.7.1
□ Test: should NOT stop below thresholds
□ Test: should stop AT thresholds
□ Test: stopping reason logged in plain language
```

### Checkpoint: Memory Operations

```
BEFORE implementing memory logic, verify:
□ Re-read Section 4.1.3 (Memory Schema)
□ Re-read Section 5.4 Anti-Patterns #8 and #9
□ Implement BOTH read (before research) and write (after research)
□ Test: similar past research influences current planning
□ Test: source effectiveness updates after each research
□ Test: access failures are permanently recorded
```

### Checkpoint: Privacy Mode

```
BEFORE implementing model selection, verify:
□ Re-read Section 1.3.6 (Privacy Mode)
□ Re-read Section 3.3 (LiteLLM Router Configuration)
□ Re-read Section 5.5 Anti-Pattern #10
□ Privacy mode is HARD CONSTRAINT never overridden
□ Test: LOCAL_ONLY mode never calls cloud API
□ Test: recommendation explains reasoning
```

### Checkpoint: Error Handling

```
BEFORE implementing any external call, verify:
□ Re-read Section 4.1.4 (Error Handling Philosophy)
□ Re-read Section 5.3 Anti-Patterns #6 and #7
□ Every exception is caught and handled explicitly
□ Every failure is logged to memory
□ Every failure is reported to user
□ Retry limits exist and are enforced
□ Graceful degradation path exists
```

### Checkpoint: Output Generation

```
BEFORE implementing report generation, verify:
□ Re-read Section 1.1 Criterion #6 (export format)
□ Re-read Section 5.6 Anti-Patterns #11 and #12
□ Report includes what was NOT found
□ Report includes access failures and reasons
□ Report includes stopping rationale
□ Report includes confidence levels
□ Test: report validates against export format spec
```

## 6.3 Phase Completion Checkpoints

### After Phase 1 (Foundation)

```
□ SwiftUI sends message to FastAPI and receives response
□ All linting passes with zero warnings
□ Test framework runs and reports coverage
□ Build produces working .app bundle
□ No code exists that violates Anti-Patterns
```

### After Phase 2 (Conversational Core)

```
□ Can converse with local Qwen model
□ Can converse with Claude API
□ Model switching works without conversation loss
□ Streaming displays tokens as they arrive
□ Response time: <2s first token local, <1s cloud
□ Privacy mode enforced correctly
□ All Anti-Patterns checked and not present
```

### After Phase 3 (Memory System)

```
□ Vector storage and retrieval works
□ Structured data storage works
□ Memory persists across app restarts
□ Retrieval latency <100ms for 10K documents
□ Source effectiveness tracking works
□ Access failure recording works
□ Anti-Patterns #8 and #9 verified not present
```

### After Phase 4 (Research Agent)

```
□ Complete research cycle executes on test query
□ Rate limiting works (tested with mock)
□ Saturation detection stops at threshold
□ Obstacles reported clearly in GUI
□ Audit trail captures all decisions
□ All search-related Anti-Patterns verified not present
```

### After Phase 5 (Intelligence Features)

```
□ Correctly identifies domain for 10 test queries
□ Recommendations match expected for test scenarios
□ Cross-verification catches planted contradictions
□ Confidence scores correlate with actual accuracy
□ Learning updates memory after each research
□ Learned knowledge influences future research
□ All Anti-Patterns verified not present
```

### After Phase 6 (Export System)

```
□ Each format produces valid, openable files
□ Templates adapt to research type
□ Large exports (1000 sources) don't crash
□ Report includes limitations section
□ Report includes stopping rationale
□ Anti-Patterns #11 and #12 verified not present
```

### After Phase 7 (Final)

```
□ All 8 Success Criteria verified with evidence
□ All Anti-Patterns verified not present
□ No critical or high-severity bugs
□ All performance benchmarks met
□ User can complete full research task without assistance
□ Memory and learning verified across multiple tasks
```

---

# PART 7: DECISION TREES

## 7.1 Model Selection Decision Tree

```
START: Need to call LLM

├── Is privacy_mode == LOCAL_ONLY?
│   ├── YES
│   │   ├── Is task_complexity == "high"?
│   │   │   ├── YES → Use "local-powerful" (Qwen2.5-32B)
│   │   │   └── NO → Use "local-fast" (Llama-3.1-8B)
│   │   └── Is local model available?
│   │       ├── YES → Proceed
│   │       └── NO → FAIL with clear error (do NOT fall back to cloud)
│   └── NO
│       ├── Is task_complexity == "high"?
│       │   ├── YES → Try "cloud-best" (Claude)
│       │   │   └── If unavailable → Fall back to "local-powerful"
│       │   └── NO
│       │       ├── Is task_complexity == "medium"?
│       │       │   ├── YES → Use "local-powerful"
│       │       │   └── NO → Use "local-fast"
│       └── Proceed with selected model
```

## 7.2 Source Selection Decision Tree

```
START: Need to search for information

├── Is query domain recognized?
│   ├── YES
│   │   ├── Load domain configuration from memory
│   │   ├── Get source effectiveness scores from memory
│   │   ├── Sort sources by (priority * effectiveness_score)
│   │   └── Use sorted order for querying
│   └── NO
│       ├── Is this a completely novel domain?
│       │   ├── YES
│       │   │   ├── Use meta-search: "how to research [domain]"
│       │   │   ├── Extract recommended sources from meta-search
│       │   │   ├── Create temporary domain configuration
│       │   │   └── Proceed with discovered sources
│       │   └── NO (partially recognized)
│       │       ├── Use closest matching domain config
│       │       ├── Add general-purpose sources (Tavily, Exa)
│       │       └── Proceed
│
├── For each source in order:
│   ├── Is source known to fail for this URL pattern?
│   │   ├── YES → Skip to next source
│   │   └── NO → Attempt query
│   │       ├── Success → Add results, continue to next source
│   │       └── Failure
│   │           ├── Is failure recoverable (rate limit, timeout)?
│   │           │   ├── YES → Retry with backoff (max 3 attempts)
│   │           │   └── NO → Record failure, continue to next source
│
└── After all sources queried:
    ├── Calculate saturation metrics
    ├── Should continue?
    │   ├── YES → Loop back with refined queries
    │   └── NO → Proceed to processing
```

## 7.3 Clarification Decision Tree

```
START: Received user query

├── Can I determine the research domain?
│   ├── YES → Continue
│   └── NO
│       ├── Are there reasonable default interpretations?
│       │   ├── YES → Pick most likely, note assumption in log
│       │   └── NO → ASK: "What field or industry is this related to?"
│
├── Can I determine the scope?
│   ├── YES → Continue
│   └── NO
│       ├── Is broad scope acceptable (won't overwhelm)?
│       │   ├── YES → Use broad scope, narrow based on results
│       │   └── NO → ASK: "Should I focus on [option A] or [option B]?"
│
├── Are there ambiguous terms?
│   ├── NO → Continue
│   └── YES
│       ├── Can I resolve from context?
│       │   ├── YES → Resolve, note in log
│       │   └── NO
│       │       ├── Will wrong interpretation waste significant effort?
│       │       │   ├── YES → ASK specific disambiguation question
│       │       │   └── NO → Pick most common interpretation, note assumption
│
├── Do I have enough to start?
│   ├── YES → BEGIN RESEARCH
│   └── NO → ASK focused question (ONE question only)

RULE: Maximum 2 clarifying exchanges before starting.
      If still unclear, start with best interpretation and note limitations.
```

## 7.4 Obstacle Handling Decision Tree

```
START: Encountered obstacle during fetch

├── What type of obstacle?
│
├── RATE_LIMIT
│   ├── Is retry-after header present?
│   │   ├── YES → Wait for specified duration, retry
│   │   └── NO → Use exponential backoff (4s, 8s, 16s, 32s, 60s max)
│   ├── After 3 retries still rate limited?
│   │   ├── YES
│   │   │   ├── Record failure in memory
│   │   │   ├── Report to user: "Source X is rate limiting, moving to alternatives"
│   │   │   └── Continue with next source
│   │   └── NO → Continue
│
├── CAPTCHA
│   ├── Is CAPTCHA solving enabled?
│   │   ├── YES
│   │   │   ├── Submit to solving service
│   │   │   ├── Wait for solution (max 60s)
│   │   │   ├── Apply solution and retry
│   │   │   └── If still blocked → Record, move to next source
│   │   └── NO
│   │       ├── Record as access failure
│   │       ├── Report to user: "Source X requires CAPTCHA, cannot access"
│   │       └── Continue with next source
│
├── PAYWALL (academic)
│   ├── Is DOI available?
│   │   ├── YES
│   │   │   ├── Query Unpaywall API
│   │   │   ├── Open access version found?
│   │   │   │   ├── YES → Use open access URL
│   │   │   │   └── NO
│   │   │   │       ├── Check arXiv/bioRxiv for preprint
│   │   │   │       ├── Found?
│   │   │   │       │   ├── YES → Use preprint (note in metadata)
│   │   │   │       │   └── NO → Record as inaccessible, log DOI for report
│   │   └── NO → Record as inaccessible
│
├── ACCESS_DENIED (403, login required)
│   ├── Record as permanent failure for this URL
│   ├── Report to user: "Cannot access [URL]: requires authentication"
│   └── Continue with next source
│
├── NOT_FOUND (404)
│   ├── Is this a known URL from citation?
│   │   ├── YES → Try web.archive.org version
│   │   └── NO → Skip, not an error
│
├── TIMEOUT
│   ├── Retry count < 3?
│   │   ├── YES → Retry with longer timeout
│   │   └── NO → Record failure, continue with next source
│
└── UNKNOWN_ERROR
    ├── Log full error details
    ├── Record in memory
    ├── Report to user: "Unexpected error accessing [source]: [brief description]"
    └── Continue with next source
```

## 7.5 Saturation Decision Tree

```
START: Completed a search cycle

├── Calculate metrics:
│   ├── new_entities_ratio = new_entities / total_entities
│   ├── new_facts_ratio = new_facts / total_facts
│   ├── citation_circularity = circular_citations / new_sources
│   └── source_coverage = completed_sources / mapped_sources
│
├── Check stopping conditions:
│
├── Is (new_entities_ratio < 0.05 AND new_facts_ratio < 0.05)?
│   ├── YES
│   │   ├── Stopping reason: "Informational saturation reached"
│   │   └── → STOP RESEARCH
│   └── NO → Continue checking
│
├── Is source_coverage > 0.95?
│   ├── YES
│   │   ├── Stopping reason: "All mapped sources exhausted"
│   │   └── → STOP RESEARCH
│   └── NO → Continue checking
│
├── Is citation_circularity > 0.80?
│   ├── YES
│   │   ├── Stopping reason: "Citation circularity - new sources reference existing findings"
│   │   └── → STOP RESEARCH
│   └── NO → Continue checking
│
├── Has user-defined limit been reached?
│   ├── YES
│   │   ├── Stopping reason: "User-defined limit reached: [limit description]"
│   │   └── → STOP RESEARCH
│   └── NO → Continue checking
│
├── Have all access methods been exhausted (all sources failing)?
│   ├── YES
│   │   ├── Stopping reason: "All accessible sources queried; remaining sources inaccessible"
│   │   └── → STOP RESEARCH
│   └── NO
│       ├── Generate refined queries based on gaps
│       └── → CONTINUE RESEARCH
```

---

# PART 8: EXPERT CODING PRACTICES

## 8.1 Development Methodology

### 8.1.1 Test-Driven Development (TDD)

**MANDATORY**: Write tests BEFORE implementation code.

```
FOR EACH FEATURE:
  1. Write failing test that defines expected behavior
  2. Implement minimum code to pass test
  3. Refactor while keeping tests green
  4. Add edge case tests
  5. Integration test with connected components
```

**Test Categories**:
| Category | Coverage Target | Tools |
|----------|-----------------|-------|
| Unit tests | 90% of business logic | pytest |
| Integration tests | All component interfaces | pytest + fixtures |
| End-to-end tests | Critical user paths | pytest + real APIs (sandboxed) |
| Performance tests | Response time benchmarks | pytest-benchmark |

### 8.1.2 Code Quality Standards

**Static Analysis** (run on every commit):
- `ruff` — Fast Python linter (replaces flake8, isort, pyupgrade)
- `mypy` — Static type checking (strict mode)
- `bandit` — Security vulnerability scanning

**Code Style**:
- Type hints on ALL function signatures
- Docstrings on ALL public functions (Google style)
- Maximum function length: 50 lines
- Maximum file length: 500 lines
- No global mutable state

**Dependency Management**:
- `uv` for package management (faster than pip)
- `pyproject.toml` for project configuration
- Lock file committed to version control
- Security audit of all dependencies before adding

### 8.1.3 Version Control Practices

**Branch Strategy**:
```
main (protected)
  └── develop
       ├── feature/[name]
       ├── bugfix/[name]
       └── refactor/[name]
```

**Commit Standards**:
- Conventional commits format: `type(scope): description`
- Types: feat, fix, refactor, test, docs, chore
- Each commit must pass all tests
- Each commit must be atomic (one logical change)

**Code Review Requirements**:
- Self-review checklist completed before marking ready
- All CI checks passing
- No decrease in test coverage

### 8.1.4 Error Handling Philosophy

**Principle**: Fail fast, fail loud, fail informatively.

```python
# WRONG - Silent failure
def fetch_data(url):
    try:
        response = requests.get(url)
        return response.json()
    except:
        return None  # Caller has no idea what went wrong

# RIGHT - Explicit, informative failure
def fetch_data(url: str) -> dict:
    """
    Fetch JSON data from URL.
    
    Raises:
        NetworkError: If connection fails
        ParseError: If response is not valid JSON
        RateLimitError: If rate limited (includes retry-after)
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.ConnectionError as e:
        raise NetworkError(f"Failed to connect to {url}: {e}") from e
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            retry_after = e.response.headers.get('Retry-After', 'unknown')
            raise RateLimitError(f"Rate limited. Retry after: {retry_after}") from e
        raise NetworkError(f"HTTP error {e.response.status_code}: {e}") from e
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON from {url}: {e}") from e
```

**Exception Hierarchy**:
```
ResearchToolError (base)
├── ConfigurationError
├── NetworkError
│   ├── RateLimitError
│   ├── AccessDeniedError
│   └── TimeoutError
├── ParseError
├── StorageError
├── ModelError
│   ├── ModelUnavailableError
│   └── ModelOverloadedError
└── ResearchError
    ├── SaturationNotReached
    └── SourceExhausted
```

### 8.1.5 Logging Standards

**Log Levels**:
| Level | Use Case | Example |
|-------|----------|---------|
| DEBUG | Detailed diagnostic info | "Parsing response from Tavily: 23 results" |
| INFO | Normal operations | "Starting research phase: Collection" |
| WARNING | Recoverable issues | "Rate limited by Semantic Scholar, backing off 60s" |
| ERROR | Operation failed | "Failed to access source: paywall detected" |
| CRITICAL | System-level failure | "Database connection lost" |

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "search_completed",
    source="tavily",
    query="drone regulations EU",
    results_count=23,
    duration_ms=450,
    new_entities=7
)
```

**Audit Trail**: All research decisions logged with reasoning for post-hoc analysis.

## 8.2 Architecture Patterns

### 8.2.1 Dependency Injection

**MANDATORY**: No hardcoded dependencies. Everything injectable for testing.

```python
# WRONG - Hardcoded dependency
class ResearchAgent:
    def __init__(self):
        self.search = TavilySearch()  # Can't test without real Tavily
        
# RIGHT - Injected dependency
class ResearchAgent:
    def __init__(self, search: SearchProvider):
        self.search = search  # Can inject mock for testing

# Usage
agent = ResearchAgent(search=TavilySearch())  # Production
agent = ResearchAgent(search=MockSearch())    # Testing
```

### 8.2.2 Interface Segregation

**All external services behind abstract interfaces** (see Section 4.2).

### 8.2.3 Repository Pattern for Storage

```python
class MemoryRepository(ABC):
    @abstractmethod
    async def store_research_result(self, result: ResearchResult) -> str:
        pass
    
    @abstractmethod
    async def query_similar(self, query: str, limit: int) -> list[ResearchResult]:
        pass

class LanceDBMemoryRepository(MemoryRepository):
    # Production implementation

class InMemoryRepository(MemoryRepository):
    # Test implementation
```

### 8.2.4 Event-Driven Progress Updates

```python
from enum import Enum
from dataclasses import dataclass

class ProgressEventType(Enum):
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    SOURCE_QUERIED = "source_queried"
    OBSTACLE_ENCOUNTERED = "obstacle_encountered"
    OBSTACLE_RESOLVED = "obstacle_resolved"
    SATURATION_UPDATE = "saturation_update"
    USER_INPUT_NEEDED = "user_input_needed"

@dataclass
class ProgressEvent:
    type: ProgressEventType
    message: str  # Plain language for GUI
    details: dict  # Structured data for logging
    timestamp: datetime

class ProgressEmitter:
    def emit(self, event: ProgressEvent):
        # Send to GUI via WebSocket
        # Log to audit trail
        # Update metrics
```

## 8.3 Reliability Patterns

### 8.3.1 Circuit Breaker for External Services

```python
from circuitbreaker import circuit

@circuit(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=NetworkError
)
async def call_tavily(query: str) -> list[SearchResult]:
    # If 5 failures in a row, circuit opens
    # After 60s, allow one test request
    # If test succeeds, circuit closes
```

### 8.3.2 Retry with Exponential Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(RateLimitError)
)
async def search_with_retry(source: SearchProvider, query: str):
    return await source.search(query)
```

### 8.3.3 Graceful Degradation

```python
async def search_all_sources(query: str) -> SearchResults:
    results = SearchResults()
    
    # Primary sources
    for source in self.primary_sources:
        try:
            results.add(await source.search(query))
        except SourceUnavailableError as e:
            results.add_unavailable_source(source.name, str(e))
            # Continue with other sources
    
    # If no primary results, try fallback sources
    if results.is_empty():
        for source in self.fallback_sources:
            try:
                results.add(await source.search(query))
            except SourceUnavailableError:
                continue
    
    # Always return something, even if just explanation of failures
    return results
```

### 8.3.4 Idempotency for State Changes

```python
async def store_research_result(self, result: ResearchResult) -> str:
    # Generate deterministic ID from content
    result_id = hash_content(result)
    
    # Check if already exists
    existing = await self.repository.get(result_id)
    if existing:
        return result_id  # Idempotent - return same ID
    
    # Store new result
    await self.repository.store(result_id, result)
    return result_id
```

### 8.3.5 Checkpointing for Long Operations

```python
class ResearchCheckpoint:
    """Allows resuming research from last good state."""
    
    async def save(self, state: ResearchState):
        await self.storage.save(
            key=f"checkpoint:{state.research_id}",
            value=state.to_dict()
        )
    
    async def load(self, research_id: str) -> Optional[ResearchState]:
        data = await self.storage.get(f"checkpoint:{research_id}")
        return ResearchState.from_dict(data) if data else None
    
    async def clear(self, research_id: str):
        await self.storage.delete(f"checkpoint:{research_id}")
```

## 8.4 Security Practices

### 8.4.1 Secrets Management

**NEVER** hardcode secrets. Use environment variables + secure storage.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    tavily_api_key: str
    anthropic_api_key: str
    exa_api_key: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Keys loaded from environment, never in code
settings = Settings()
```

### 8.4.2 Input Validation

```python
from pydantic import BaseModel, validator

class ResearchRequest(BaseModel):
    query: str
    max_sources: int = 50
    privacy_mode: PrivacyMode = PrivacyMode.RECOMMEND
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        if len(v) > 10000:
            raise ValueError('Query too long (max 10000 chars)')
        return v.strip()
    
    @validator('max_sources')
    def reasonable_max(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('max_sources must be between 1 and 1000')
        return v
```

### 8.4.3 Output Sanitization

Before displaying any external content in GUI:
- Escape HTML entities
- Validate URLs before making them clickable
- Truncate excessively long strings
- Remove potential script injection

---

# PART 9: BUILD PROCESS SAFEGUARDS

## 9.1 Phased Delivery with Validation Gates

Each phase MUST pass its validation gate before next phase begins.

### Phase 1: Foundation
**Deliverables**:
- Project structure with all configurations
- SwiftUI shell with FastAPI backend connected
- Basic message sending/receiving working
- All development tooling configured (tests, linting, CI)

**Validation Gate**: See Section 6.3

### Phase 2: Conversational Core
**Deliverables**:
- LiteLLM integration with Ollama and Claude
- Basic conversation handling
- Model selection logic (manual first, then automatic)
- Streaming responses to GUI

**Validation Gate**: See Section 6.3

### Phase 3: Memory System
**Deliverables**:
- LanceDB integration for vector storage
- SQLite for structured data
- Memory storage and retrieval
- Basic learning (store what worked)

**Validation Gate**: See Section 6.3

### Phase 4: Research Agent
**Deliverables**:
- LangGraph workflow implementation
- All search tool integrations
- OSINT intelligence cycle implementation
- Obstacle handling (rate limits, CAPTCHAs, paywalls)
- Saturation detection and stopping logic

**Validation Gate**: See Section 6.3

### Phase 5: Intelligence Features
**Deliverables**:
- Auto-configuration based on query analysis
- Privacy mode recommendation
- Cross-verification logic
- Confidence scoring
- Learning updates after each research task

**Validation Gate**: See Section 6.3

### Phase 6: Export System
**Deliverables**:
- All export formats implemented
- Template system with contextual selection
- Export validation

**Validation Gate**: See Section 6.3

### Phase 7: Polish and Integration
**Deliverables**:
- End-to-end testing
- Performance optimization
- Documentation
- Edge case handling

**Validation Gate**: See Section 6.3

## 9.2 Risk Register and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SwiftUI-Python communication issues | Medium | High | Prototype communication layer first; have fallback to Tauri if needed |
| Ollama Metal performance issues | Low | High | Test on actual hardware before committing; have cloud fallback |
| LangGraph complexity | Medium | Medium | Start with simple workflow; add complexity incrementally |
| Search API changes/deprecation | Medium | Medium | Abstract behind interfaces; have multiple providers |
| Memory scaling issues | Low | Medium | Benchmark with large datasets early; have cleanup strategies |
| Model quality insufficient | Medium | High | Test with real research tasks; have model upgrade path |
| Integration complexity | High | Medium | Build incrementally with integration tests at each step |

## 9.3 Rollback Strategy

If a phase fails validation after multiple attempts:

1. **First attempt**: Debug and fix within phase
2. **Second attempt**: Simplify scope while maintaining core functionality
3. **Third attempt**: Rollback to previous phase; reassess approach
4. **Escalation**: Present situation to user with options

**Rollback procedure**:
```
1. Tag current state: git tag failed-phase-X-attempt-Y
2. Reset to last validated phase: git reset --hard phase-(X-1)-validated
3. Document what went wrong in DECISIONS.md
4. Propose alternative approach before proceeding
```

## 9.4 Quality Metrics

Track these metrics throughout development:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test coverage | >90% | pytest-cov |
| Type coverage | 100% | mypy --strict |
| Lint warnings | 0 | ruff |
| Security issues | 0 critical/high | bandit |
| Response time (local) | <2s first token | Benchmark tests |
| Response time (cloud) | <1s first token | Benchmark tests |
| Memory retrieval | <100ms | Benchmark tests |
| Research completion | <5min typical query | End-to-end tests |

## 9.5 Definition of Done

A feature is DONE when:

- [ ] Implementation complete
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Type hints complete and mypy passes
- [ ] Docstrings complete
- [ ] No lint warnings
- [ ] Security scan clean
- [ ] Performance benchmarks met
- [ ] GUI integration tested
- [ ] Error handling tested (happy path AND failure modes)
- [ ] Logging adequate for debugging
- [ ] Self-review checklist completed
- [ ] Relevant Anti-Patterns verified not present
- [ ] Relevant Verification Checkpoints completed

---

# PART 10: VERIFICATION MASTER CHECKLIST

Before presenting build plan to user, verify against this checklist:

## 10.1 Requirements Coverage

- [ ] All 8 success criteria have corresponding implementation plan
- [ ] All user rules respected in process design
- [ ] All operational behaviors have technical implementation
- [ ] Auto-configuration with learning implemented
- [ ] Professional methodology (OSINT cycle) implemented
- [ ] All obstacle handling methods included
- [ ] Stopping criteria implemented
- [ ] Memory and learning system complete
- [ ] Privacy mode with intelligent recommendation implemented

## 10.2 Technical Decisions Honored

- [ ] SwiftUI for GUI (not Tauri)
- [ ] Python backend with FastAPI
- [ ] LangGraph for agent workflow
- [ ] Single ReAct agent (not multi-agent)
- [ ] LiteLLM for model orchestration
- [ ] Ollama native (not Docker)
- [ ] LanceDB for vectors
- [ ] SQLite for structured data
- [ ] All specified search tools included
- [ ] All export formats included

## 10.3 Embedded Research Applied

- [ ] LangGraph patterns from Section 3.1 used
- [ ] Ollama configuration from Section 3.2 applied
- [ ] LiteLLM Router from Section 3.3 implemented
- [ ] LanceDB hybrid search from Section 3.4 implemented
- [ ] Search tool configs from Section 3.5 used
- [ ] Obstacle handling from Section 3.6 implemented
- [ ] Saturation detection from Section 3.7 implemented

## 10.4 Code Skeletons Followed

- [ ] Data structures from Section 4.1 used
- [ ] Interfaces from Section 4.2 implemented
- [ ] LangGraph workflow from Section 4.3 followed
- [ ] SwiftUI-Python communication from Section 4.4 implemented

## 10.5 Anti-Patterns Addressed

- [ ] All 12 anti-patterns have prevention mechanisms
- [ ] Tests exist to catch each anti-pattern
- [ ] Code review checklist includes anti-pattern verification

## 10.6 Verification Checkpoints Included

- [ ] Pre-implementation checkpoints in workflow
- [ ] Component-specific checkpoints documented
- [ ] Phase completion checkpoints enforced

## 10.7 Decision Trees Implemented

- [ ] Model selection decision tree in code
- [ ] Source selection decision tree in code
- [ ] Clarification decision tree in code
- [ ] Obstacle handling decision tree in code
- [ ] Saturation decision tree in code

## 10.8 Expert Practices Included

- [ ] TDD mandated
- [ ] Static analysis configured
- [ ] Dependency injection pattern
- [ ] Interface segregation for external services
- [ ] Error handling philosophy documented
- [ ] Logging standards defined
- [ ] Circuit breaker for external services
- [ ] Retry with backoff
- [ ] Graceful degradation
- [ ] Checkpointing for long operations
- [ ] Security practices defined

## 10.9 Build Process Safeguards

- [ ] Phased delivery with validation gates
- [ ] Risk register with mitigations
- [ ] Rollback strategy defined
- [ ] Quality metrics tracked
- [ ] Definition of Done clear and comprehensive

---

# PART 11: DOCUMENT CONTROL

**Version**: 2.0
**Status**: AWAITING USER CONFIRMATION
**Created**: 2025-12-06
**Last Modified**: 2025-12-06

## Change Log

| Version | Date | Changes | Approved By |
|---------|------|---------|-------------|
| 1.0 | 2025-12-06 | Initial creation | Pending |
| 2.0 | 2025-12-06 | Added: Embedded Research (Part 3), Code Skeletons (Part 4), Anti-Patterns (Part 5), Verification Checkpoints (Part 6), Decision Trees (Part 7), Enhanced verification checklist (Part 10) | Pending |

## Self-Assessment

This document now contains:
- ✅ All requirements from v1.0 (unchanged)
- ✅ Distilled research findings with concrete technical details
- ✅ Code skeletons with data structures, interfaces, state definitions
- ✅ 12 explicit anti-patterns with wrong/right examples
- ✅ Verification checkpoints for each component and phase
- ✅ 5 decision trees for ambiguous situations
- ✅ All expert coding practices from v1.0 (unchanged)
- ✅ All build process safeguards from v1.0 (unchanged)
- ✅ Comprehensive verification master checklist

## Approval

This document requires explicit user confirmation before build plan creation.

**User Confirmation**: [ ] CONFIRMED / [ ] REQUIRES CHANGES

---

*END OF META BUILD GUIDE v2.0*
