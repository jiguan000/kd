#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/backend"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-}"

if [[ -n "$RELOAD" ]]; then
  exec uvicorn app.main:app --reload --host "$HOST" --port "$PORT"
else
  exec uvicorn app.main:app --host "$HOST" --port "$PORT"
fi
