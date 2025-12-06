# PHASE 3: MEMORY SYSTEM
## Detailed Implementation Guide

**Prerequisites**: 
- Phase 2 complete and validated
- Branch: `git checkout -b phase-3-memory develop`

**Tasks**: TODO.md #95-135

**Estimated Duration**: 3-4 hours

---

## 1. OBJECTIVES

By the end of Phase 3:
- [ ] LanceDB vector storage operational
- [ ] SQLite structured storage operational
- [ ] Memory repository interface implemented
- [ ] Source effectiveness tracking working
- [ ] Access failure recording working
- [ ] Retrieval latency <100ms for 10K documents

---

## 2. MEMORY REPOSITORY INTERFACE

### 2.1 Abstract Interface

**File**: `/backend/src/research_tool/services/memory/repository.py`

```python
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime


class MemoryRepository(ABC):
    """Abstract interface for memory operations."""
    
    @abstractmethod
    async def store_document(
        self,
        content: str,
        metadata: dict,
        session_id: str
    ) -> str:
        """Store document with embedding. Returns document ID."""
        pass
    
    @abstractmethod
    async def search_similar(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> list[dict]:
        """Search for similar documents using hybrid search."""
        pass
    
    @abstractmethod
    async def get_source_effectiveness(
        self,
        source_name: str,
        domain: Optional[str] = None
    ) -> float:
        """Get effectiveness score for a source (0.0 to 1.0)."""
        pass
    
    @abstractmethod
    async def update_source_effectiveness(
        self,
        source_name: str,
        domain: str,
        success: bool,
        quality_score: float
    ) -> None:
        """Update source effectiveness using EMA."""
        pass
    
    @abstractmethod
    async def record_access_failure(
        self,
        url: str,
        source_name: str,
        error_type: str,
        error_message: str
    ) -> None:
        """Record permanent access failure."""
        pass
    
    @abstractmethod
    async def is_known_failure(self, url: str) -> bool:
        """Check if URL is known to be inaccessible."""
        pass
```

---

## 3. LANCEDB IMPLEMENTATION

### 3.1 Schema Definition

From META guide Section 3.4:

```python
import lancedb
from lancedb.pydantic import LanceModel, Vector


class ResearchDocument(LanceModel):
    """Document stored in LanceDB."""
    id: str
    content: str
    vector: Vector(384)  # bge-small-en-v1.5
    session_id: str
    source_url: Optional[str]
    source_name: Optional[str]
    domain: Optional[str]
    created_at: datetime
    metadata: dict
```

### 3.2 Embedding Model

From META guide Section 3.4.1:
- Model: `BAAI/bge-small-en-v1.5`
- Dimension: 384
- Library: sentence-transformers

```python
from sentence_transformers import SentenceTransformer

class LanceDBRepository:
    def __init__(self):
        self.embedder = SentenceTransformer('BAAI/bge-small-en-v1.5')
        self.db = lancedb.connect("./data/lance_db")
```

### 3.3 Hybrid Search

From META guide Section 3.4.2:

```python
async def search_similar(
    self,
    query: str,
    limit: int = 10,
    filters: Optional[dict] = None
) -> list[dict]:
    """
    Hybrid search: 60% semantic + 40% keyword.
    """
    # Get query embedding
    query_vector = self.embedder.encode(query)
    
    # Semantic search
    table = self.db.open_table("research_documents")
    semantic_results = table.search(query_vector).limit(limit * 2).to_list()
    
    # Keyword search (FTS)
    keyword_results = table.search(query, query_type="fts").limit(limit * 2).to_list()
    
    # Combine with weighted scoring
    combined = self._merge_results(
        semantic_results, 
        keyword_results,
        semantic_weight=0.6,
        keyword_weight=0.4
    )
    
    return combined[:limit]
```

### 3.4 Chunking Strategy

From META guide Section 3.4.3:

```python
def chunk_document(self, text: str) -> list[str]:
    """
    Chunk document for embedding.
    - Target: 512 tokens
    - Overlap: 64 tokens
    """
    # Use tiktoken or similar for accurate token counting
    chunks = []
    words = text.split()
    chunk_size = 400  # Approximate words for 512 tokens
    overlap = 50      # Approximate words for 64 tokens
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    
    return chunks
```

---

## 4. SQLITE IMPLEMENTATION

### 4.1 Schema

From META guide Section 4.1.3:

```sql
-- Research sessions
CREATE TABLE research_sessions (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    domain TEXT,
    privacy_mode TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    saturation_metrics TEXT,  -- JSON
    final_report_path TEXT
);

-- Source effectiveness tracking
CREATE TABLE source_effectiveness (
    source_name TEXT NOT NULL,
    domain TEXT NOT NULL,
    effectiveness_score REAL NOT NULL DEFAULT 0.5,
    total_queries INTEGER NOT NULL DEFAULT 0,
    successful_queries INTEGER NOT NULL DEFAULT 0,
    avg_quality_score REAL,
    last_updated TIMESTAMP NOT NULL,
    PRIMARY KEY (source_name, domain)
);

-- Access failures (permanent record)
CREATE TABLE access_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT,
    first_failed_at TIMESTAMP NOT NULL,
    retry_count INTEGER DEFAULT 1
);

-- Domain configuration overrides (learned)
CREATE TABLE domain_config_overrides (
    domain TEXT PRIMARY KEY,
    preferred_sources TEXT,  -- JSON array
    excluded_sources TEXT,   -- JSON array
    custom_keywords TEXT,    -- JSON array
    updated_at TIMESTAMP NOT NULL
);

-- User preferences
CREATE TABLE user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### 4.2 Implementation

**File**: `/backend/src/research_tool/services/memory/sqlite_repo.py`

```python
import sqlite3
import aiosqlite
from pathlib import Path


class SQLiteRepository:
    def __init__(self, db_path: str = "./data/research.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Create tables if not exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA_SQL)
            await db.commit()
    
    async def record_access_failure(
        self,
        url: str,
        source_name: str,
        error_type: str,
        error_message: str
    ) -> None:
        """Record permanent access failure."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO access_failures 
                (url, source_name, error_type, error_message, first_failed_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                ON CONFLICT(url) DO UPDATE SET retry_count = retry_count + 1
                """,
                (url, source_name, error_type, error_message)
            )
            await db.commit()
```

---

## 5. SOURCE EFFECTIVENESS LEARNING

### 5.1 Exponential Moving Average

From META guide Section 3.7:

```python
class SourceLearning:
    """Track and learn source effectiveness."""
    
    ALPHA = 0.3  # EMA smoothing factor
    
    async def update_effectiveness(
        self,
        source_name: str,
        domain: str,
        success: bool,
        quality_score: float,
        repo: SQLiteRepository
    ) -> None:
        """
        Update source effectiveness using exponential moving average.
        
        new_score = α * current_result + (1-α) * old_score
        """
        # Get current score
        current = await repo.get_source_effectiveness(source_name, domain)
        if current is None:
            current = 0.5  # Default neutral score
        
        # Calculate new score
        result_score = quality_score if success else 0.0
        new_score = self.ALPHA * result_score + (1 - self.ALPHA) * current
        
        # Update in database
        await repo.set_source_effectiveness(source_name, domain, new_score)
```

### 5.2 Source Ranking

```python
async def get_ranked_sources(
    self,
    domain: str,
    available_sources: list[str]
) -> list[tuple[str, float]]:
    """
    Get sources ranked by effectiveness for domain.
    
    Returns list of (source_name, effectiveness_score) tuples.
    """
    scores = []
    for source in available_sources:
        score = await self.repo.get_source_effectiveness(source, domain)
        if score is None:
            score = 0.5  # Default for unknown
        scores.append((source, score))
    
    # Sort by score descending
    return sorted(scores, key=lambda x: x[1], reverse=True)
```

---

## 6. COMBINED MEMORY REPOSITORY

### 6.1 Composite Implementation

**File**: `/backend/src/research_tool/services/memory/combined_repo.py`

```python
class CombinedMemoryRepository(MemoryRepository):
    """Combines LanceDB and SQLite for full memory system."""
    
    def __init__(self):
        self.lance = LanceDBRepository()
        self.sqlite = SQLiteRepository()
        self.learning = SourceLearning()
    
    async def initialize(self):
        """Initialize both stores."""
        await self.sqlite.initialize()
        # LanceDB initializes on first use
    
    async def store_document(self, content: str, metadata: dict, session_id: str) -> str:
        """Store in LanceDB with embedding."""
        return await self.lance.store_document(content, metadata, session_id)
    
    async def search_similar(self, query: str, limit: int = 10, filters: dict = None):
        """Hybrid search in LanceDB."""
        return await self.lance.search_similar(query, limit, filters)
    
    async def get_source_effectiveness(self, source: str, domain: str = None) -> float:
        """Get from SQLite."""
        return await self.sqlite.get_source_effectiveness(source, domain)
    
    async def update_source_effectiveness(self, source: str, domain: str, success: bool, quality: float):
        """Update via learning system."""
        await self.learning.update_effectiveness(source, domain, success, quality, self.sqlite)
    
    async def record_access_failure(self, url: str, source: str, error_type: str, message: str):
        """Record in SQLite."""
        await self.sqlite.record_access_failure(url, source, error_type, message)
    
    async def is_known_failure(self, url: str) -> bool:
        """Check SQLite."""
        return await self.sqlite.is_known_failure(url)
```

---

## 7. ANTI-PATTERN PREVENTION

### 7.1 Anti-Pattern #8: Not Using Memory for Planning

From META guide Section 5.4:

```python
# WRONG
async def plan_research(query: str) -> ResearchPlan:
    return create_generic_plan(query)

# RIGHT
async def plan_research(query: str, memory: MemoryRepository) -> ResearchPlan:
    # Check for similar past research
    past_research = await memory.search_similar(query, limit=5)
    
    # Get source effectiveness for domain
    domain = detect_domain(query)
    source_scores = await memory.get_ranked_sources(domain)
    
    # Check known failures
    blocked_urls = await memory.get_failed_urls()
    
    return create_informed_plan(query, past_research, source_scores, blocked_urls)
```

### 7.2 Anti-Pattern #9: Not Updating Memory After Research

```python
# WRONG
async def complete_research(state: ResearchState) -> Report:
    report = generate_report(state)
    return report  # Memory never updated!

# RIGHT
async def complete_research(state: ResearchState, memory: MemoryRepository) -> Report:
    report = generate_report(state)
    
    # Update source effectiveness for each source used
    for source_result in state.all_sources:
        await memory.update_source_effectiveness(
            source_name=source_result.source,
            domain=state.domain,
            success=source_result.success,
            quality_score=source_result.quality
        )
    
    # Record any access failures permanently
    for failure in state.access_failures:
        await memory.record_access_failure(
            url=failure.url,
            source_name=failure.source,
            error_type=failure.error_type,
            error_message=failure.message
        )
    
    # Store research for future reference
    await memory.store_document(
        content=report.summary,
        metadata={"query": state.query, "domain": state.domain},
        session_id=state.session_id
    )
    
    return report
```

---

## 8. TESTS

### 8.1 LanceDB Tests

```python
async def test_store_and_retrieve_document():
    """Documents can be stored and retrieved."""
    repo = LanceDBRepository()
    doc_id = await repo.store_document("Test content", {"key": "value"}, "session-1")
    results = await repo.search_similar("Test content", limit=1)
    assert len(results) == 1
    assert results[0]["id"] == doc_id

async def test_hybrid_search_finds_relevant():
    """Hybrid search returns semantically similar documents."""
    # Store documents
    # Search with related query
    # Verify relevant documents returned

async def test_chunking_produces_correct_sizes():
    """Chunking respects 512 token target with 64 overlap."""
```

### 8.2 SQLite Tests

```python
async def test_access_failure_recording():
    """Access failures are recorded and retrievable."""

async def test_source_effectiveness_update():
    """Source effectiveness updates correctly."""

async def test_persistence_across_restart():
    """Data persists when repository is recreated."""
```

### 8.3 Performance Tests

```python
@pytest.mark.benchmark
async def test_retrieval_latency_10k_docs():
    """Retrieval should be <100ms for 10K documents."""
    repo = LanceDBRepository()
    
    # Store 10K documents
    for i in range(10000):
        await repo.store_document(f"Document {i} content", {}, "session")
    
    # Measure retrieval time
    start = time.time()
    results = await repo.search_similar("test query", limit=10)
    elapsed = time.time() - start
    
    assert elapsed < 0.1  # 100ms
```

---

## 9. VALIDATION GATE

Before proceeding to Phase 4:

```
□ LanceDB stores and retrieves documents
  → Unit tests pass

□ SQLite stores structured data
  → Unit tests pass

□ Hybrid search returns relevant results
  → Test with known data

□ Source effectiveness tracks correctly
  → EMA calculation verified

□ Access failures recorded permanently
  → Persist across restart

□ Retrieval <100ms for 10K docs
  → Benchmark test passes

□ Anti-patterns #8 and #9 NOT present
  → Code review completed
```

---

## 10. COMMIT AND MERGE

```bash
git add .
git commit -m "feat: complete phase 3 memory system [BUILD-PLAN Phase 3]"
git checkout develop
git merge phase-3-memory
git push origin develop
```

---

*END OF PHASE 3 GUIDE*
