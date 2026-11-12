#!/usr/bin/env bash
# Full integration with REAL Postgres and three independent Node services.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo "Docker Engine + Docker Compose v2 required"; exit 1; }
command -v python3 >/dev/null || { echo "Python >=3.10 required"; exit 1; }
python3 tools/init_env.py
docker compose config --quiet
docker compose up -d --build
python3 tools/verify.py
echo "PASS real PostgreSQL persistence + frontend/backend/redirector service integration"
echo "Containers remain for inspection; run docker compose down for cleanup."
echo "Use docker compose down -v ONLY to intentionally delete the learning database."
