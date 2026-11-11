#!/usr/bin/env bash
# Requires the running Docker Compose Kafka/Postgres/Influx stack from Lab 13-C.
# This tests only the HTTP callback contract; actual KafkaSource/Knative is Lab 13-E.
set -euo pipefail
cd "$(dirname "$0")/.."
test -f .env || { echo "Run python3 tools/init_env.py and docker compose up first" >&2; exit 1; }
python3 - <<'PY'
import socket,sys
with socket.socket() as s:
  try: s.bind(("127.0.0.1",5081))
  except OSError as err: sys.exit(f"Port 5081 busy: {err}")
PY
set -a
. .env
set +a
export POSTGRES_CONNECTION="Host=127.0.0.1;Port=5433;Database=globex;Username=globex;Password=$PG_PASSWORD"
export INFLUX_URL=http://127.0.0.1:8086
export INFLUX_ORG=globex
export INFLUX_BUCKET=review_sentiment
export KAFKA_BOOTSTRAP=127.0.0.1:9092
dotnet build src/GlobexReviews/GlobexReviews.csproj -c Release
work="$(mktemp -d)"
pid=""
cleanup() {
  if test -n "$pid"; then kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; fi
  rm -rf -- "$work"
}
trap cleanup EXIT
ASPNETCORE_URLS=http://127.0.0.1:5080 REVIEWS_MODE=knative  dotnet src/GlobexReviews/bin/Release/net10.0/GlobexReviews.dll > "$work/app.log" 2>&1 &
pid="$!"
for i in $(seq 1 30); do
  if python3 - <<'PY'
import urllib.request,sys
try:
  with urllib.request.urlopen("http://127.0.0.1:5080/healthz",timeout=1) as r: assert r.status==200
except Exception: sys.exit(1)
PY
  then break; fi
  if test "$i" -eq 30; then cat "$work/app.log"; exit 1; fi
  sleep 1
done
python3 tools/verify_knative_callbacks.py
python3 tools/check_external.py --minimum-approved 3
echo "PASS Knative-style CloudEvent HTTP callback contract (not live Knative)"
