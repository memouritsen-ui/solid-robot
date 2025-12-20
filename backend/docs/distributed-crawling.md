# Distributed Crawling

Distributed crawling allows you to scale URL crawling across multiple workers using Celery and Redis.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   FastAPI   │────▶│    Redis     │────▶│  Celery Worker  │
│  /api/crawl │     │  (broker +   │     │  (crawl task)   │
│   /batch    │     │   results)   │     └─────────────────┘
└─────────────┘     └──────────────┘     ┌─────────────────┐
                           │────────────▶│  Celery Worker  │
                           │             │  (crawl task)   │
                           │             └─────────────────┘
                           │             ┌─────────────────┐
                           └────────────▶│  Celery Worker  │
                                         │  (crawl task)   │
                                         └─────────────────┘
```

## Quick Start

### 1. Start Infrastructure

```bash
cd backend

# Start Redis + 2 workers + Flower monitoring
./scripts/start-distributed.sh

# Or with custom worker count
./scripts/start-distributed.sh 4  # 4 workers
```

### 2. Verify Redis is Running

```bash
# Check Redis
redis-cli ping
# PONG

# Check distributed availability
curl http://localhost:8000/api/crawl/distributed/status
# {"distributed_available": true, "message": "Redis connected"}
```

### 3. Use the Batch Crawl API

```bash
# Crawl multiple URLs with distributed workers
curl -X POST http://localhost:8000/api/crawl/batch \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com",
      "https://httpbin.org/html",
      "https://jsonplaceholder.typicode.com"
    ],
    "distributed": true,
    "timeout": 300
  }'
```

Response:
```json
{
  "session_id": "abc123...",
  "results": [
    {"status": "success", "url": "https://example.com", "content": "...", "worker_id": "worker-1"},
    {"status": "success", "url": "https://httpbin.org/html", "content": "...", "worker_id": "worker-2"}
  ],
  "stats": {
    "total": 3,
    "success": 3,
    "failed": 0,
    "workers_used": 2
  },
  "distributed": true
}
```

## API Reference

### POST /api/crawl/batch

Crawl multiple URLs in batch (local or distributed).

**Request Body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `urls` | `list[str]` | required | URLs to crawl |
| `distributed` | `bool` | `false` | Use distributed crawling |
| `options` | `dict` | `{}` | Crawl options |
| `timeout` | `float` | `300.0` | Timeout in seconds |

**Response:**

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `str` | Unique session ID |
| `results` | `list[dict]` | Crawl results with status, url, content |
| `stats` | `dict \| null` | Stats (only with distributed=true) |
| `distributed` | `bool` | Whether distributed was used |

### GET /api/crawl/distributed/status

Check if distributed crawling is available.

**Response:**

```json
{
  "distributed_available": true,
  "message": "Redis connected"
}
```

## Configuration

Environment variables for distributed crawling:

| Variable | Default | Description |
|----------|---------|-------------|
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Redis broker URL |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Redis results URL |
| `CELERY_TASK_RATE_LIMIT` | `10/m` | Tasks per minute per worker |
| `CELERY_TASK_MAX_RETRIES` | `3` | Max retries on failure |
| `CELERY_WORKER_CONCURRENCY` | `2` | Concurrent tasks per worker |

## Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| `redis` | 6379 | Message broker and result backend |
| `celery-worker` | - | Crawl worker (default: 2 instances) |
| `flower` | 5555 | Celery monitoring dashboard |

## Monitoring

Flower provides a web UI for monitoring Celery tasks:

```
http://localhost:5555
```

Features:
- Active/completed/failed task counts
- Worker status and health
- Task execution details
- Rate limiting stats

## Scaling Workers

```bash
# Scale to 8 workers
docker compose -f docker-compose.distributed.yml up -d --scale celery-worker=8

# Check worker count
docker compose -f docker-compose.distributed.yml ps
```

## Stopping

```bash
docker compose -f docker-compose.distributed.yml down

# Remove volumes too
docker compose -f docker-compose.distributed.yml down -v
```

## Local vs Distributed

| Feature | Local (`distributed=false`) | Distributed (`distributed=true`) |
|---------|------------------------------|----------------------------------|
| Speed | Sequential | Parallel across workers |
| Scale | Single machine | Multiple workers/machines |
| Rate limiting | None | Per-worker rate limits |
| Retry | None | Automatic with backoff |
| Monitoring | Logs only | Flower dashboard |
| Requirement | None | Redis + Docker |

## Troubleshooting

### Redis not available
```
{"distributed_available": false, "message": "Redis not available"}
```

**Solution:** Start Redis with `docker compose -f docker-compose.distributed.yml up -d redis`

### Workers not picking up tasks

1. Check worker logs: `docker compose -f docker-compose.distributed.yml logs celery-worker`
2. Check Redis connection: `redis-cli ping`
3. Check task registration: Look in Flower dashboard

### Tasks stuck in queue

1. Check worker concurrency (default: 2)
2. Check rate limits (default: 10/minute)
3. Scale up workers if needed
