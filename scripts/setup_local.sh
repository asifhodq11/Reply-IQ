#!/usr/bin/env bash
# ============================================================
# ReplyIQ Backend — Local Development Setup
# Run this once after cloning: bash scripts/setup_local.sh
# ============================================================

set -e

echo "=== ReplyIQ Local Setup ==="

# 1. Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# 2. Activate (for this script session)
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null

# 3. Install dependencies
echo "Installing production dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Installing dev dependencies..."
pip install -r requirements-dev.txt

# 4. Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# 5. Create .env if missing
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "IMPORTANT: Edit .env with your real API keys before running."
else
    echo ".env already exists."
fi

# 6. Verify environment
echo "Verifying environment..."
python scripts/verify_env.py

echo ""
echo "=== Setup Complete ==="
echo "Activate your environment: source .venv/bin/activate (or .venv\\Scripts\\activate on Windows)"
echo "Run the app: make run"
