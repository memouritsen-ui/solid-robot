#!/bin/bash
cd "$(dirname "$0")/../backend"
uv run uvicorn research_tool.main:app --reload --host 127.0.0.1 --port 8000
