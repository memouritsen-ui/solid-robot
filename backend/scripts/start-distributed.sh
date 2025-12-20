#!/bin/bash
# Start distributed crawling infrastructure
# Usage: ./scripts/start-distributed.sh [workers]

set -e

WORKERS=${1:-2}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

echo "Starting distributed crawling infrastructure..."
echo "  - Redis: localhost:6379"
echo "  - Workers: $WORKERS"
echo "  - Flower (monitoring): http://localhost:5555"

# Start Redis and Flower
docker compose -f docker-compose.distributed.yml up -d redis flower

# Wait for Redis to be healthy
echo "Waiting for Redis..."
until docker compose -f docker-compose.distributed.yml exec -T redis redis-cli ping 2>/dev/null; do
    sleep 1
done
echo "Redis is ready!"

# Scale workers
echo "Starting $WORKERS workers..."
docker compose -f docker-compose.distributed.yml up -d --scale celery-worker=$WORKERS

echo ""
echo "Distributed crawling infrastructure is running!"
echo "  - Test Redis: redis-cli ping"
echo "  - Monitor: http://localhost:5555"
echo "  - Stop: docker compose -f docker-compose.distributed.yml down"
