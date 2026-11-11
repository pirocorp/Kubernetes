#!/usr/bin/env bash
# Repeatable local acceptance test. Run from any working directory.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v dotnet >/dev/null || { echo ".NET 10 SDK missing" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Python 3.10+ missing" >&2; exit 1; }
python3 - <<'PY'
import socket
import sys
for port in (8080, 8081, 8082):
    try:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", port))
    except OSError as error:
        sys.exit(f"Port {port} already in use: {error}. Stop the existing service first.")
print("PASS: ports 8080, 8081, 8082 available")
PY
test "$(dotnet --version | cut -d. -f1)" = "10" || {
  echo ".NET 10 SDK required, not merely an installed runtime" >&2; exit 1;
}

work="$(mktemp -d)"
mock_pid="" api_pid="" gateway_pid=""
cleanup() {
  for pid in "$gateway_pid" "$api_pid" "$mock_pid"; do
    if test -n "$pid"; then kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; fi
  done
  rm -rf -- "$work"
  unset API_KEY ADMIN_KEY API_UPSTREAM || true
}
trap cleanup EXIT INT TERM

export API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
export ADMIN_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
export API_UPSTREAM="http://127.0.0.1:8080"

# No external Python dependencies.
python3 -m compileall -q tools
python3 -m json.tool contract/products-v1.openapi.json >/dev/null
dotnet build src/ProductsApi/ProductsApi.csproj -c Release

wait_health() {
  local port="$1" expected="$2"
  for i in $(seq 1 30); do
    if python3 - "$port" "$expected" <<'PY'
import sys, urllib.request
port, expected = int(sys.argv[1]), sys.argv[2]
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=1) as r:
        assert r.status == 200 and r.read().decode().strip() == expected
except Exception:
    sys.exit(1)
PY
    then return 0; fi
    sleep 1
  done
  echo "Service on port $port did not become healthy" >&2
  return 1
}

python3 tools/mock_server.py > "$work/mock.log" 2>&1 &
mock_pid="$!"
wait_health 8082 ok || { cat "$work/mock.log"; exit 1; }
python3 tools/contract_check.py --base-url http://127.0.0.1:8082
kill "$mock_pid" 2>/dev/null || true; wait "$mock_pid" 2>/dev/null || true; mock_pid=""

ASPNETCORE_URLS=http://127.0.0.1:8080 dotnet run \
  --project src/ProductsApi/ProductsApi.csproj \
  -c Release --no-build --no-launch-profile > "$work/api.log" 2>&1 &
api_pid="$!"
wait_health 8080 ok || { cat "$work/api.log"; exit 1; }
python3 tools/contract_check.py --base-url http://127.0.0.1:8080

python3 tools/gateway.py > "$work/gateway.log" 2>&1 &
gateway_pid="$!"
# Gateway does not expose /healthz. Wait for a 401 without credentials.
for i in $(seq 1 30); do
  if python3 - <<'PY'
import urllib.error, urllib.request, sys
try:
    urllib.request.urlopen("http://127.0.0.1:8081/v1/products", timeout=1)
except urllib.error.HTTPError as err:
    sys.exit(0 if err.code == 401 else 1)
except Exception:
    sys.exit(1)
sys.exit(1)
PY
  then break; fi
  if test "$i" -eq 30; then cat "$work/gateway.log"; exit 1; fi
  sleep 1
done

python3 - <<'PY'
import json
import os
import urllib.error
import urllib.request
base = "http://127.0.0.1:8081"
key = os.environ["API_KEY"]
admin = os.environ["ADMIN_KEY"]
def get(path, header=None):
    req = urllib.request.Request(base + path, headers=header or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
for i in range(4):
    code, _ = get("/v1/products", {"X-Api-Key": key})
    expected = 200 if i < 3 else 429
    assert code == expected, (i, code, expected)
metrics_code, raw = get("/_metrics", {"X-Admin-Key": admin})
assert metrics_code == 200, metrics_code
metrics = json.loads(raw)
assert metrics["requests"] >= 3 and metrics["limited"] >= 1, metrics
denied, _ = get("/_metrics")
assert denied == 401
print("PASS: API Management 401/200/429 and admin-only metrics")
PY
echo "PASS: Module 10 local acceptance suite (mock, actual .NET API, gateway)"
