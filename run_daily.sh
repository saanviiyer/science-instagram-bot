#!/bin/bash
# Daily draft run. Invoked by the LaunchAgent (or run by hand to test).
# Loads .env (API key / IG tokens) if present, drafts all topic accounts,
# and logs to drafts/_logs/<date>.log.

set -euo pipefail
PROJECT_DIR="/Users/saanviiyer/Downloads/CALTECH/science-instagram-bot"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

cd "$PROJECT_DIR"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

mkdir -p drafts/_logs
LOG="drafts/_logs/$(date +%Y-%m-%d).log"

{
  echo "==== run $(date) ===="
  "$PYTHON" -m src.pipeline draft --all --limit 2 --within-days 30
  # Uncomment to also draft institution accounts each day:
  # "$PYTHON" -m src.pipeline --config institutions draft --all --limit 2 --within-days 45

  # Host new cards on GitHub Pages + write public image_urls (only if configured).
  if [ -n "${GITHUB_USER:-}" ]; then
    "$PYTHON" -m src.host || echo "host step skipped/failed"
  fi
  echo "==== done $(date) ===="
} >> "$LOG" 2>&1
