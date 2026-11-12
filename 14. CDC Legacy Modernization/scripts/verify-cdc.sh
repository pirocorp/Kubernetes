#!/usr/bin/env bash
# Real, self-contained Docker-based CDC acceptance from clean local checkout.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo "Docker Engine/Compose v2 required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Python 3.10+ required" >&2; exit 1; }
python3 tools/init_env.py
# Docker Compose loads .env for interpolation but standalone register_connector.py
# reads PG_PASSWORD from the process environment. Export it explicitly.
set -a
. .env
set +a
docker compose config --quiet
# Build the two runtime roles from the same C# code; legacy code does not publish Kafka.
docker compose up -d --build
python3 tools/register_connector.py
python3 tools/verify.py
python3 tools/check_infra.py
echo "PASS Module 14 REAL Postgres WAL / Debezium / Kafka / Elasticsearch / cashback integration"
echo "Services and volumes left running for manual review."
echo "Cleanup containers: docker compose down"
echo "Cleanup lab data ONLY when intentionally chosen: docker compose down -v"
