#!/bin/bash
cd "$(dirname "$0")/../backend"

echo "=== Running Tests ==="
uv run pytest tests/ -v --cov=src/research_tool --cov-report=term-missing

echo "=== Running Linter ==="
uv run ruff check .

echo "=== Running Type Check ==="
uv run mypy src/

echo "=== Running Security Scan ==="
uv run bandit -r src/
