#!/bin/bash
set -e

echo "=== Research Tool Setup ==="

# Check prerequisites
command -v uv >/dev/null 2>&1 || { echo "uv required. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
command -v ollama >/dev/null 2>&1 || { echo "ollama required. Install: brew install ollama"; exit 1; }

# Setup Python backend
echo "Setting up Python backend..."
cd "$(dirname "$0")/../backend"
uv sync
uv pip install -e ".[dev]"

# Install playwright browsers
echo "Installing Playwright browsers..."
uv run playwright install chromium

# Create .env if not exists
if [ ! -f .env ]; then
    cp ../.env.example .env
    echo "Created .env from template. Please add your API keys."
fi

echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Add API keys to backend/.env"
echo "2. Run: ./scripts/start_ollama.sh"
echo "3. Run: ./scripts/start_backend.sh"
echo "4. Open gui/ResearchTool in Xcode and run"
