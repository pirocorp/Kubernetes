#!/usr/bin/env bash
# One-command source/build/real HTTP check, without Kafka/Docker/cluster prerequisites.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v dotnet >/dev/null || { echo ".NET 10 SDK missing" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Python 3.10+ missing" >&2; exit 1; }
test "$(dotnet --version | cut -d. -f1)" = "10" || {
  echo "The exercise requires .NET SDK 10" >&2; exit 1;
}
python3 - <<'PY'
import socket,sys
with socket.socket() as s:
    try: s.bind(("127.0.0.1", 5080))
    except OSError as err: sys.exit(f"Port 5080 busy: {err}")
print("PASS port 5080 available")
PY
work="$(mktemp -d)"
pid=""
cleanup() {
  if test -n "$pid"; then
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  fi
  rm -rf -- "$work"
}
trap cleanup EXIT
python3 -m compileall -q tools
python3 -m json.tool contracts/review-submitted.json >/dev/null
dotnet build src/GlobexReviews/GlobexReviews.csproj -c Release
ASPNETCORE_URLS=http://127.0.0.1:5080 REVIEWS_MODE=local   dotnet src/GlobexReviews/bin/Release/net10.0/GlobexReviews.dll > "$work/api.log" 2>&1 &
pid="$!"
for attempt in $(seq 1 30); do
  if python3 - <<'PY'
import urllib.request,sys
try:
    with urllib.request.urlopen("http://127.0.0.1:5080/healthz",timeout=1) as response:
        assert response.status==200 and response.read()==b"ok"
except Exception: sys.exit(1)
PY
  then break; fi
  if test "$attempt" = "30"; then cat "$work/api.log"; exit 1; fi
  sleep 1
done
python3 tools/verify.py --base-url http://127.0.0.1:5080
echo "PASS Module 14 local C# event processing, moderation and sentiment"
