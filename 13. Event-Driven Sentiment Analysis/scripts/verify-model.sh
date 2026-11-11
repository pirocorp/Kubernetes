#!/usr/bin/env bash
# Actual HTTP model boundary test against the included deterministic fixture.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v dotnet >/dev/null && command -v python3 >/dev/null || {
  echo "Requires .NET 10 SDK and Python 3.10+" >&2; exit 1;
}
python3 - <<'PY'
import socket,sys
for port in (5080,8090):
    with socket.socket() as s:
        try: s.bind(("127.0.0.1",port))
        except OSError as error: sys.exit(f"Port {port} busy: {error}")
PY
dotnet build src/GlobexReviews/GlobexReviews.csproj -c Release
work="$(mktemp -d)"
api_pid="" model_pid=""
cleanup() {
  for pid in "$api_pid" "$model_pid"; do
    if test -n "$pid"; then kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; fi
  done
  rm -rf -- "$work"
}
trap cleanup EXIT
python3 tools/mock_model.py > "$work/model.log" 2>&1 &
model_pid="$!"
ASPNETCORE_URLS=http://127.0.0.1:5080 REVIEWS_MODE=local SENTIMENT_MODEL_URL=http://127.0.0.1:8090/predict   dotnet run --no-build -c Release --no-launch-profile   --project src/GlobexReviews/GlobexReviews.csproj > "$work/api.log" 2>&1 &
api_pid="$!"
for i in $(seq 1 30); do
  if python3 - <<'PY'
import urllib.request,sys
try:
    with urllib.request.urlopen("http://127.0.0.1:5080/healthz",timeout=1) as r: assert r.status==200
    with urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8090/predict",data=b'{"text":"great"}',headers={"Content-Type":"application/json"}),timeout=1) as r: assert r.status==200
except Exception: sys.exit(1)
PY
  then break; fi
  if test "$i" -eq 30; then cat "$work/api.log" "$work/model.log"; exit 1; fi
  sleep 1
done
python3 tools/verify.py --base-url http://127.0.0.1:5080 --expect-model python-fixture-NOT-ML
echo "PASS real HTTP inference boundary (fixture explicitly NOT trained ML)"
