#!/usr/bin/env bash
# run.sh - one-command start for macOS and Linux.
# Creates the virtual environment, installs Flask, creates .env, then starts the app.
set -e
cd "$(dirname "$0")"

PY=python3
command -v python3 >/dev/null 2>&1 || PY=python

if [ ! -d .venv ]; then
  echo "Creating virtual environment (.venv)..."
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

if ! python -c "import flask" 2>/dev/null; then
  echo "Installing dependencies..."
  pip install -r requirements.txt
fi

[ -f .env ] || cp .env.example .env

echo ""
echo "DreamPath AI is starting at http://127.0.0.1:${PORT:-5000}   (press Ctrl+C to stop)"
echo ""
exec flask --app app run --debug --port "${PORT:-5000}"
