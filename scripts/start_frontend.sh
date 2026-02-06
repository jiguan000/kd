#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-5173}"
API_BASE="${API_BASE:-http://localhost:8000}"
CONFIG_FILE="$FRONTEND_DIR/config.local.js"

cat > "$CONFIG_FILE" <<CONFIG
window.API_BASE = "${API_BASE}";
CONFIG

echo "[frontend] API_BASE set to: ${API_BASE}"
python -m http.server "$PORT" --bind "$HOST" --directory "$FRONTEND_DIR"
