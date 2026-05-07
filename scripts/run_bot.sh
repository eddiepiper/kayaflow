#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Verify .env exists
if [[ ! -f ".env" ]]; then
  echo "ERROR: .env file not found. Copy .env.example to .env and fill in your keys."
  exit 1
fi

# Check virtual environment
if [[ -d "venv" ]]; then
  source venv/bin/activate
fi

echo "Starting KayaFlow bot..."
python -m bot.telegram_bot
