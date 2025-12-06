# PHASE 4: RESEARCH AGENT
## Detailed Implementation Guide

**Prerequisites**: 
- Phase 3 complete and validated
- Branch: `git checkout -b phase-4-research develop`

**Tasks**: TODO.md #136-204

**Estimated Duration**: 5-6 hours (largest phase)

---

## 1. OBJECTIVES

By the end of Phase 4:
- [ ] All data models implemented (ResearchState, Entity, Fact, etc.)
- [ ] All search providers working (Tavily, Exa, Semantic Scholar, PubMed, arXiv, Unpaywall, Brave, Playwright)
- [ ] Rate limiting per provider
- [ ] Obstacle handling (rate limits, CAPTCHAs, paywalls, timeouts)
- [ ] LangGraph agent with all nodes
- [ ] Saturation detection working
- [ ] Research API endpoints operational
- [ ] Complete research cycle executes successfully

---

## 2. DATA MODELS

### 2.1 Research State

From META guide Section 4.1:

**File**: `/backend/src/research_tool/models/state.py`

```python
from typing import Annotated, Optional
from typing_extensions import TypedDict
from operator import add
from datetime import datetime


class ResearchState(TypedDict):
    """State maintained throughout research workflow."""
    
    # Immutable
    session_id: str
    original_query: str
    privacy_mode: str  # "local_only", "cloud_allowed", "hybrid"
    started_at: datetime
    
    # Refined during clarification
    refined_query: str
    domain: str
    
    # Accumulating (use Annotated for LangGraph accumulation)
    sources_queried: Annotated[list[str], add]
    entities_found: Annotated[list[dict], add]
    facts_extracted: Annotated[list[dict], add]
    access_failures: Annotated[list[dict], add]
    
    # Current state
    current_phase: str
    saturation_metrics: Optional[dict]
    should_stop: bool
    stop_reason: Optional[str]
    
    # Output
    final_report: Optional[dict]
    export_path: Optional[str]
```

### 2.2 Domain Configuration

**File**: `/backend/src/research_tool/models/domain.py`

```python
from dataclasses import dataclass


@dataclass
class DomainConfiguration:
    """Per-domain source configuration."""
    
    domain: str
    primary_sources: list[str]
    secondary_sources: list[str]
    academic_required: bool
    verification_threshold: float
    keywords: list[str]
    excluded_sources: list[str]
    
    @classmethod
    def for_medical(cls) -> "DomainConfiguration":
        return cls(
            domain="medical",
            primary_sources=["pubmed", "semantic_scholar"],
            secondary_sources=["arxiv", "google_scholar"],
            academic_required=True,
            verification_threshold=0.8,
            keywords=["clinical", "patient", "treatment", "diagnosis", "therapy"],
            excluded_sources=["wikipedia"]
        )
    
    @classmethod
    def for_competitive_intelligence(cls) -> "DomainConfiguration":
        return cls(
            domain="competitive_intelligence",
            primary_sources=["tavily", "exa", "brave"],
            secondary_sources=["news_api", "crunchbase"],
            academic_required=False,
            verification_threshold=0.6,
            keywords=["company", "market", "competitor", "funding", "product"],
            excluded_sources=[]
        )
```

### 2.3 Entity and Fact Models

**File**: `/backend/src/research_tool/models/entities.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SourceResult:
    """Single result from a search source."""
    url: str
    title: str
    snippet: str
    source_name: str
    retrieved_at: datetime
    full_content: Optional[str] = None
    quality_score: float = 0.5
    
    
@dataclass
class Entity:
    """Extracted entity with provenance."""
    name: str
    entity_type: str  # person, organization, product, etc.
    sources: list[str]  # URLs where found
    first_seen: datetime
    mention_count: int = 1
    

@dataclass
class Fact:
    """Verified fact with confidence."""
    statement: str
    sources: list[str]
    confidence: float  # 0.0 to 1.0
    verified: bool
    contradictions: list[str]  # Conflicting statements found
```

---

## 3. SEARCH PROVIDERS

### 3.1 Provider Interface

**File**: `/backend/src/research_tool/services/search/provider.py`

```python
from abc import ABC, abstractmethod
from typing import Optional


class SearchProvider(ABC):
    """Abstract interface for search providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this provider."""
        pass
    
    @property
    @abstractmethod
    def requests_per_second(self) -> float:
        """Rate limit for this provider."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        filters: Optional[dict] = None
    ) -> list[dict]:
        """Execute search and return results."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is configured and accessible."""
        pass
```

### 3.2 Rate Limiter

**File**: `/backend/src/research_tool/services/search/rate_limiter.py`

From META guide Section 3.5.2:

```python
import asyncio
from collections import defaultdict
from time import time


class RateLimiter:
    """Token bucket rate limiter per provider."""
    
    def __init__(self):
        self._last_request: dict[str, float] = defaultdict(float)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
    
    async def acquire(self, provider: str, requests_per_second: float) -> None:
        """Wait until request is allowed."""
        async with self._locks[provider]:
            min_interval = 1.0 / requests_per_second
            elapsed = time() - self._last_request[provider]
            
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            
            self._last_request[provider] = time()


# Global instance
rate_limiter = RateLimiter()
```

### 3.3 Tavily Provider

**File**: `/backend/src/research_tool/services/search/tavily.py`

```python
from tavily import TavilyClient
from research_tool.core import Settings
from .provider import SearchProvider
from .rate_limiter import rate_limiter

settings = Settings()


class TavilyProvider(SearchProvider):
    """Tavily search provider."""
    
    @property
    def name(self) -> str:
        return "tavily"
    
    @property
    def requests_per_second(self) -> float:
        return 5.0  # Generous limit
    
    def __init__(self):
        self.client = TavilyClient(api_key=settings.tavily_api_key)
    
    async def search(self, query: str, max_results: int = 10, filters: dict = None) -> list[dict]:
        await rate_limiter.acquire(self.name, self.requests_per_second)
        
        response = self.client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_raw_content=True
        )
        
        return [
            {
                "url": r["url"],
                "title": r["title"],
                "snippet": r["content"],
                "source_name": self.name,
                "full_content": r.get("raw_content")
            }
            for r in response.get("results", [])
        ]
    
    async def is_available(self) -> bool:
        return settings.tavily_api_key is not None
```

### 3.4 Semantic Scholar Provider

**File**: `/backend/src/research_tool/services/search/semantic_scholar.py`

From META guide Section 3.5.2 — **CRITICAL: 1 RPS limit**

```python
import httpx
from .provider import SearchProvider
from .rate_limiter import rate_limiter


class SemanticScholarProvider(SearchProvider):
    """Semantic Scholar provider with strict rate limiting."""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    @property
    def name(self) -> str:
        return "semantic_scholar"
    
    @property
    def requests_per_second(self) -> float:
        return 1.0  # CRITICAL: Do not exceed!
    
    async def search(self, query: str, max_results: int = 10, filters: dict = None) -> list[dict]:
        await rate_limiter.acquire(self.name, self.requests_per_second)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/paper/search",
                params={
                    "query": query,
                    "limit": max_results,
                    "fields": "title,abstract,url,authors,year,citationCount"
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
        
        return [
            {
                "url": f"https://www.semanticscholar.org/paper/{p['paperId']}",
                "title": p.get("title", ""),
                "snippet": p.get("abstract", ""),
                "source_name": self.name,
                "metadata": {
                    "authors": p.get("authors", []),
                    "year": p.get("year"),
                    "citations": p.get("citationCount")
                }
            }
            for p in data.get("data", [])
        ]
    
    async def is_available(self) -> bool:
        return True  # No API key required for basic access
```

### 3.5 Other Providers

Implement similarly for:
- **exa.py** — Exa AI search
- **pubmed.py** — PubMed medical literature
- **arxiv.py** — arXiv preprints
- **unpaywall.py** — Open access finder
- **brave.py** — Brave Search API
- **crawler.py** — Playwright with stealth

Each must:
1. Implement `SearchProvider` interface
2. Respect rate limits
3. Handle errors gracefully
4. Return standardized result format

---

## 4. OBSTACLE HANDLING

### 4.1 Retry Logic

**File**: `/backend/src/research_tool/utils/retry.py`

From META guide Section 3.6:

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from research_tool.core.exceptions import RateLimitError, TimeoutError


def with_retry(func):
    """Decorator for retry with exponential backoff."""
    return retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((RateLimitError, TimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            "retry_attempt",
            attempt=retry_state.attempt_number,
            wait=retry_state.next_action.sleep
        )
    )(func)
```

### 4.2 Circuit Breaker

**File**: `/backend/src/research_tool/utils/circuit_breaker.py`

```python
from enum import Enum
from datetime import datetime, timedelta


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Prevent cascade failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure: datetime | None = None
    
    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure = datetime.now()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def record_success(self) -> None:
        self.failures = 0
        self.state = CircuitState.CLOSED
    
    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure > timedelta(seconds=self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        
        # HALF_OPEN - allow one request
        return True
```

### 4.3 Obstacle Handler

**File**: `/backend/src/research_tool/agent/decisions/obstacle_handler.py`

From META guide Section 7.4:

```python
from research_tool.core.exceptions import (
    RateLimitError, AccessDeniedError, TimeoutError
)
from research_tool.core import get_logger

logger = get_logger(__name__)


class ObstacleHandler:
    """Handle obstacles per decision tree."""
    
    async def handle(
        self,
        error: Exception,
        source_name: str,
        url: str,
        memory
    ) -> str:
        """
        Handle obstacle and return action.
        
        Returns: "retry", "skip", "fallback", "abort"
        """
        if isinstance(error, RateLimitError):
            logger.info("rate_limit_hit", source=source_name, retry_after=error.retry_after)
            # Decision tree: rate_limit → exponential backoff → retry
            return "retry"
        
        elif isinstance(error, AccessDeniedError):
            # Decision tree: access_denied → record failure → try next source
            await memory.record_access_failure(
                url=url,
                source_name=source_name,
                error_type="access_denied",
                error_message=str(error)
            )
            return "skip"
        
        elif isinstance(error, TimeoutError):
            # Decision tree: timeout → retry with longer timeout (max 3)
            return "retry"
        
        else:
            # Unknown error
            logger.error("unknown_obstacle", source=source_name, error=str(error))
            return "skip"
```

---

## 5. LANGGRAPH AGENT

### 5.1 Graph Definition

**File**: `/backend/src/research_tool/agent/graph.py`

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from research_tool.models.state import ResearchState
from research_tool.agent.nodes import (
    clarify_node,
    plan_node,
    collect_node,
    process_node,
    analyze_node,
    evaluate_node,
    synthesize_node,
    export_node
)


def create_research_graph():
    """Create the research workflow graph."""
    
    # Initialize graph with state type
    workflow = StateGraph(ResearchState)
    
    # Add nodes
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("collect", collect_node)
    workflow.add_node("process", process_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("synthesize", synthesize_node)
    workflow.add_node("export", export_node)
    
    # Define edges
    workflow.set_entry_point("clarify")
    
    workflow.add_edge("clarify", "plan")
    workflow.add_edge("plan", "collect")
    workflow.add_edge("collect", "process")
    workflow.add_edge("process", "analyze")
    workflow.add_edge("analyze", "evaluate")
    
    # Conditional edge: evaluate → synthesize or collect
    workflow.add_conditional_edges(
        "evaluate",
        should_continue,
        {
            "continue": "collect",
            "stop": "synthesize"
        }
    )
    
    workflow.add_edge("synthesize", "export")
    workflow.add_edge("export", END)
    
    # Add checkpointing
    memory = SqliteSaver.from_conn_string("./data/checkpoints.db")
    
    return workflow.compile(checkpointer=memory)


def should_continue(state: ResearchState) -> str:
    """Decide whether to continue collecting or synthesize."""
    if state.get("should_stop", False):
        return "stop"
    return "continue"
```

### 5.2 Node Implementations

Each node follows this pattern:

```python
async def node_name(state: ResearchState) -> dict:
    """
    Node description.
    
    Receives: Current state
    Returns: State updates (partial dict)
    """
    # Do work
    result = await do_something(state)
    
    # Return only the fields to update
    return {
        "field_to_update": result,
        "current_phase": "node_name"
    }
```

**Key nodes**:

1. **clarify_node** — Analyze query, ask if genuinely blocked (MAX 2 exchanges)
2. **plan_node** — Create research plan using memory
3. **collect_node** — Query sources per plan
4. **process_node** — Extract entities and facts
5. **analyze_node** — Cross-verify and score confidence
6. **evaluate_node** — Calculate saturation metrics
7. **synthesize_node** — Generate report
8. **export_node** — Export to requested format

---

## 6. SATURATION DETECTION

### 6.1 Metrics Calculation

**File**: `/backend/src/research_tool/agent/decisions/saturation.py`

From META guide Section 3.7:

```python
from dataclasses import dataclass


@dataclass
class SaturationMetrics:
    """Metrics for determining research saturation."""
    new_entities_ratio: float      # New entities / Total entities
    new_facts_ratio: float         # New facts / Total facts
    citation_circularity: float    # Self-referencing citation ratio
    source_coverage: float         # Sources queried / Available sources


def calculate_saturation(
    entities_before: int,
    entities_after: int,
    facts_before: int,
    facts_after: int,
    circular_citations: int,
    total_citations: int,
    sources_queried: int,
    sources_available: int
) -> SaturationMetrics:
    """Calculate saturation metrics."""
    
    new_entities = entities_after - entities_before
    new_facts = facts_after - facts_before
    
    return SaturationMetrics(
        new_entities_ratio=new_entities / max(entities_after, 1),
        new_facts_ratio=new_facts / max(facts_after, 1),
        citation_circularity=circular_citations / max(total_citations, 1),
        source_coverage=sources_queried / max(sources_available, 1)
    )


def should_stop(metrics: SaturationMetrics) -> tuple[bool, str]:
    """
    Determine if research should stop.
    
    From META guide Section 7.5:
    - Stop if new_entities_ratio < 0.05
    - Stop if new_facts_ratio < 0.05
    - Stop if source_coverage > 0.95
    - Continue if any metric above threshold
    
    Returns: (should_stop, reason)
    """
    if metrics.new_entities_ratio < 0.05:
        return True, "Entity saturation reached (<5% new entities in last cycle)"
    
    if metrics.new_facts_ratio < 0.05:
        return True, "Fact saturation reached (<5% new facts in last cycle)"
    
    if metrics.source_coverage > 0.95:
        return True, "Source coverage complete (>95% of available sources queried)"
    
    if metrics.citation_circularity > 0.80:
        return True, "High citation circularity (>80% circular references)"
    
    return False, "Saturation not yet reached, continuing research"
```

---

## 7. RESEARCH API

### 7.1 Endpoints

**File**: `/backend/src/research_tool/api/routes/research.py`

```python
from fastapi import APIRouter, BackgroundTasks, WebSocket
from research_tool.agent.graph import create_research_graph
from research_tool.models.requests import ResearchRequest, ResearchStatus

router = APIRouter(prefix="/api/research", tags=["research"])

# Active research sessions
active_sessions: dict[str, dict] = {}


@router.post("/start")
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start a new research task."""
    session_id = str(uuid.uuid4())
    
    # Initialize state
    initial_state = {
        "session_id": session_id,
        "original_query": request.query,
        "privacy_mode": request.privacy_mode,
        "started_at": datetime.now(),
        "current_phase": "starting",
        "sources_queried": [],
        "entities_found": [],
        "facts_extracted": [],
        "access_failures": [],
        "should_stop": False
    }
    
    active_sessions[session_id] = {
        "state": initial_state,
        "status": "running"
    }
    
    # Run in background
    background_tasks.add_task(run_research, session_id, initial_state)
    
    return {"session_id": session_id, "status": "started"}


@router.get("/{session_id}/status")
async def get_status(session_id: str) -> ResearchStatus:
    """Get current research status."""
    if session_id not in active_sessions:
        raise HTTPException(404, "Session not found")
    
    session = active_sessions[session_id]
    return ResearchStatus(
        session_id=session_id,
        status=session["status"],
        current_phase=session["state"].get("current_phase"),
        sources_queried=len(session["state"].get("sources_queried", [])),
        entities_found=len(session["state"].get("entities_found", [])),
        saturation_metrics=session["state"].get("saturation_metrics")
    )


@router.post("/{session_id}/stop")
async def stop_research(session_id: str):
    """Stop research early."""
    if session_id not in active_sessions:
        raise HTTPException(404, "Session not found")
    
    active_sessions[session_id]["state"]["should_stop"] = True
    active_sessions[session_id]["state"]["stop_reason"] = "User requested stop"
    
    return {"status": "stopping"}
```

### 7.2 Progress WebSocket

**File**: `/backend/src/research_tool/api/websocket/progress_ws.py`

```python
from fastapi import WebSocket

async def research_progress_websocket(websocket: WebSocket, session_id: str):
    """Stream research progress updates."""
    await websocket.accept()
    
    try:
        while True:
            if session_id not in active_sessions:
                await websocket.send_json({"type": "error", "message": "Session not found"})
                break
            
            session = active_sessions[session_id]
            
            # Send current status
            await websocket.send_json({
                "type": "progress",
                "phase": session["state"].get("current_phase"),
                "sources_queried": len(session["state"].get("sources_queried", [])),
                "entities_found": len(session["state"].get("entities_found", [])),
                "message": get_plain_language_status(session["state"])
            })
            
            if session["status"] in ("completed", "failed"):
                await websocket.send_json({
                    "type": "complete",
                    "status": session["status"],
                    "result": session.get("result")
                })
                break
            
            await asyncio.sleep(1)  # Update every second
            
    except WebSocketDisconnect:
        pass
```

---

## 8. ANTI-PATTERN PREVENTION

### 8.1 Anti-Pattern #3: Stopping Too Early

```python
# WRONG
if sources_queried >= 3:
    return synthesize()  # Arbitrary limit!

# RIGHT
metrics = calculate_saturation(...)
should_stop, reason = check_saturation(metrics)
if should_stop:
    logger.info("stopping_research", reason=reason, metrics=asdict(metrics))
    return synthesize()
```

### 8.2 Anti-Pattern #4: Stopping Too Late

```python
# WRONG
# No saturation check, just keep going until all sources exhausted

# RIGHT
# Check saturation AFTER EACH CYCLE
for cycle in range(MAX_CYCLES):
    results = await collect_from_sources()
    metrics = calculate_saturation(...)
    if should_stop(metrics):
        break  # Don't waste resources
```

### 8.3 Anti-Pattern #5: Ignoring Source Quality

```python
# WRONG
sources = ["tavily", "exa", "semantic_scholar"]  # Fixed order

# RIGHT
source_scores = await memory.get_ranked_sources(domain)
sources = [s[0] for s in sorted(source_scores, key=lambda x: x[1], reverse=True)]
```

### 8.4 Anti-Pattern #6: Silent Failure

```python
# WRONG
try:
    result = await search(query)
except Exception:
    pass  # Silent failure!

# RIGHT
try:
    result = await search(query)
except Exception as e:
    logger.error("search_failed", source=source, error=str(e))
    await memory.record_access_failure(url, source, type(e).__name__, str(e))
    raise  # Or handle explicitly
```

### 8.5 Anti-Pattern #7: Infinite Retry

```python
# WRONG
while True:
    try:
        result = await search(query)
        break
    except:
        continue  # Forever!

# RIGHT
@retry(stop=stop_after_attempt(5), wait=wait_exponential(max=60))
async def search_with_retry(query):
    return await search(query)
```

---

## 9. TESTS

### 9.1 Search Provider Tests

```python
async def test_tavily_search_returns_results():
    """Tavily returns structured results."""
    
async def test_semantic_scholar_respects_rate_limit():
    """Semantic Scholar waits between requests."""
    
async def test_provider_handles_errors_gracefully():
    """Errors don't crash the provider."""
```

### 9.2 Saturation Tests

```python
def test_saturation_detected_at_threshold():
    """Saturation triggers when metrics below threshold."""
    metrics = SaturationMetrics(
        new_entities_ratio=0.03,  # Below 5%
        new_facts_ratio=0.10,
        citation_circularity=0.5,
        source_coverage=0.8
    )
    should_stop, reason = check_saturation(metrics)
    assert should_stop
    assert "entity" in reason.lower()

def test_research_continues_above_threshold():
    """Research continues when metrics above threshold."""
```

### 9.3 Agent Workflow Tests

```python
async def test_complete_research_cycle():
    """Full research cycle completes successfully."""
    graph = create_research_graph()
    result = await graph.ainvoke({
        "original_query": "What are the latest treatments for diabetes?",
        "privacy_mode": "cloud_allowed",
        ...
    })
    assert result["final_report"] is not None
```

---

## 10. VALIDATION GATE

```
□ All search providers return results
□ Rate limiting prevents API abuse
□ Obstacles handled per decision tree
□ Saturation detection works correctly
□ LangGraph workflow executes completely
□ API endpoints respond correctly
□ WebSocket streams progress
□ Anti-patterns #3-7 NOT present
□ Audit trail captures all decisions
```

---

## 11. COMMIT AND MERGE

```bash
git add .
git commit -m "feat: complete phase 4 research agent [BUILD-PLAN Phase 4]"
git checkout develop
git merge phase-4-research
git push origin develop
```

---

*END OF PHASE 4 GUIDE*
