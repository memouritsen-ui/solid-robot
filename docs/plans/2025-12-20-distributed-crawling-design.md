# Distributed Crawling Design

**Date:** 2025-12-20
**Status:** Approved
**Author:** Claude + Mads

## Summary

Add distributed crawling capability to solid-robot using Celery + Redis, enabling horizontal scaling from local Docker containers to cloud deployment.

## Requirements

- **Speed**: Crawl 100+ URLs faster via parallelization
- **Scale**: Handle systematic reviews with 1000+ sources
- **Resilience**: Worker failures don't stop the crawl
- **IP Diversity**: Multiple workers = multiple IPs for rate limit avoidance

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Deployment | Hybrid (local → cloud) | Start simple, scale when needed |
| Task Queue | Celery + Redis | Battle-tested, great ecosystem |
| Workers | 8+ (configurable) | M4 Max has resources |
| Integration | Explicit `distributed=True` | Full user control |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     solid-robot Backend                      │
│  ┌─────────────┐                                            │
│  │ Research API │──── distributed=False ───→ Direct Crawler │
│  │   /crawl     │──── distributed=True ────┐                │
│  └─────────────┘                           │                │
└────────────────────────────────────────────┼────────────────┘
                                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     Celery + Redis                          │
│  ┌──────────┐    ┌─────────────┐    ┌─────────────────┐    │
│  │  Redis   │◄───│ Task Queue  │◄───│ Result Backend  │    │
│  │ :6379    │    │ (URLs)      │    │ (crawled data)  │    │
│  └──────────┘    └─────────────┘    └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
    ┌────┴────┐    ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
    │Worker 1 │    │Worker 2 │   │Worker 3 │   │Worker N │
    │Playwright│    │Playwright│   │Playwright│   │Playwright│
    └─────────┘    └─────────┘   └─────────┘   └─────────┘
```

## File Structure

```
backend/src/research_tool/
├── services/
│   └── distributed/
│       ├── __init__.py
│       ├── celery_app.py
│       ├── tasks.py
│       ├── coordinator.py
│       └── config.py
│
├── api/routes/
│   └── crawl.py  (modified)

docker/
├── docker-compose.distributed.yml
├── Dockerfile.worker
└── worker-entrypoint.sh
```

## Core Components

### 1. Celery Task (`tasks.py`)

```python
@app.task(bind=True, base=CrawlTask, max_retries=3, rate_limit='10/m')
def crawl_url(self, url: str, session_id: str, options: dict) -> dict:
    """Crawl single URL with retry and rate limiting."""
```

Features:
- Browser reuse across tasks
- Exponential backoff on rate limits
- Structured result format

### 2. Coordinator (`coordinator.py`)

```python
class CrawlCoordinator:
    async def crawl_many(urls, options, on_progress) -> list[dict]:
        """Distribute URLs and aggregate results."""
```

Features:
- Progress callbacks for WebSocket updates
- Handles partial failures gracefully
- Statistics on workers used

### 3. API Endpoint (`crawl.py`)

```python
@router.post("/batch")
async def crawl_batch(request: CrawlRequest):
    if request.distributed:
        # Use Celery workers
    else:
        # Direct crawling
```

## Docker Configuration

### docker-compose.distributed.yml

- **Redis**: Message broker + result backend
- **Workers**: 8 replicas, 2GB memory limit each
- **Flower**: Optional monitoring UI on :5555

### Dockerfile.worker

- Python 3.11 slim base
- Playwright + Chromium pre-installed
- Browser cache in volume for reuse

## Usage

### Start Infrastructure

```bash
docker compose -f docker/docker-compose.distributed.yml up -d --scale worker=8
```

### API Call

```bash
curl -X POST localhost:8000/api/crawl/batch \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example1.com", "https://example2.com", ...],
    "session_id": "research-123",
    "distributed": true
  }'
```

### Monitor

- Flower UI: http://localhost:5555
- Redis CLI: `docker exec -it redis redis-cli`

## Dependencies

```toml
[project.optional-dependencies]
distributed = [
    "celery[redis]>=5.3.0",
    "redis>=5.0.0",
    "flower>=2.0.0",
]
```

## Future Enhancements

- Cloud deployment templates (AWS ECS, GCP Cloud Run)
- Auto-scaling based on queue depth
- Per-domain rate limiting in coordinator
- Result streaming via WebSocket

## Testing Strategy

1. Unit tests for coordinator logic
2. Integration tests with Redis testcontainer
3. E2E test with 2 workers in CI

---

*Approved: 2025-12-20*
