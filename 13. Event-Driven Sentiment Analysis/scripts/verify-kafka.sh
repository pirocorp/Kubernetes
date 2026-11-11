#!/usr/bin/env bash
# Requires Docker Compose and .NET SDK 10. Keeps containers for dashboard inspection.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo "Docker + Compose required" >&2; exit 1; }
command -v dotnet >/dev/null || { echo ".NET 10 SDK required" >&2; exit 1; }
python3 tools/init_env.py
set -a
. .env
set +a
docker compose up -d kafka postgres influxdb grafana
# Docker health and Kafka startup occur asynchronously.
for i in $(seq 1 60); do
  if docker compose exec -T postgres pg_isready -U globex -d globex >/dev/null 2>&1 &&
    docker compose exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null 2>&1 &&
    python3 - <<'PY'
import urllib.request,sys
try:
    with urllib.request.urlopen("http://127.0.0.1:8086/health",timeout=2) as r: assert r.status == 200
except Exception: sys.exit(1)
PY
  then break; fi
  if test "$i" -eq 60; then docker compose ps; echo "Dependency readiness failed" >&2; exit 1; fi
  sleep 2
done
dotnet build src/GlobexReviews/GlobexReviews.csproj -c Release
work="$(mktemp -d)"
pid=""
cleanup() {
  if test -n "$pid"; then kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; fi
  rm -rf -- "$work"
}
trap cleanup EXIT
export POSTGRES_CONNECTION="Host=127.0.0.1;Port=5433;Database=globex;Username=globex;Password=$PG_PASSWORD"
export INFLUX_URL="http://127.0.0.1:8086"
export INFLUX_ORG="globex"
export INFLUX_BUCKET="review_sentiment"
export KAFKA_BOOTSTRAP="127.0.0.1:9092"
ASPNETCORE_URLS=http://127.0.0.1:5080 REVIEWS_MODE=kafka   dotnet src/GlobexReviews/bin/Release/net10.0/GlobexReviews.dll > "$work/api.log" 2>&1 &
pid="$!"
for i in $(seq 1 45); do
  if python3 - <<'PY'
import urllib.request,sys
try:
    with urllib.request.urlopen("http://127.0.0.1:5080/healthz",timeout=2) as r: assert r.status==200
except Exception: sys.exit(1)
PY
  then break; fi
  if test "$i" -eq 45; then cat "$work/api.log"; exit 1; fi
  sleep 1
done
python3 tools/verify.py --base-url http://127.0.0.1:5080 --timeout 60
python3 tools/check_external.py --minimum-approved 3
python3 tools/check_grafana.py
TOPICS="$(docker compose exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list)"
KAFKA_GROUP_LIST="$(docker compose exec -T kafka /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list)"
printf '%s\n' "$TOPICS"
printf '%s\n' "$KAFKA_GROUP_LIST"
for topic in globex.reviews reviews.moderated reviews.denied reviews.sentiment; do
  grep -Fqx "$topic" <<< "$TOPICS" || { echo "Missing Kafka topic $topic" >&2; exit 1; }
done
for group in m13-moderation m13-sentiment; do
  grep -Fqx "$group" <<< "$KAFKA_GROUP_LIST" || { echo "Missing Kafka consumer group $group" >&2; exit 1; }
done
echo "PASS real Kafka fan-out, PostgreSQL, InfluxDB and provisioned Grafana"
echo "Grafana: http://127.0.0.1:3300 (admin credentials in local .env)."
echo "Cleanup: docker compose down ; docker compose down -v ONLY if you want to delete demo volumes."
