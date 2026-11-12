#!/usr/bin/env bash
# Module 12 local acceptance suite. Requires .NET 10, Python 3.10+, ports 8080/8081.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v dotnet >/dev/null || { echo ".NET 10 SDK missing" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Python 3.10+ missing" >&2; exit 1; }
test "$(dotnet --version | cut -d. -f1)" = "10" || { echo ".NET 10 SDK required" >&2; exit 1; }
python3 - <<'PY'
import socket, sys
for port in (8080, 8081):
    try:
        with socket.socket() as s:
            s.bind(("127.0.0.1", port))
    except OSError as ex:
        sys.exit(f"Port {port} busy: {ex}")
print("PASS: ports 8080, 8081 free")
PY
if test -e .runtime/lifecycle.json; then
  echo ".runtime/lifecycle.json exists: preserve the user's existing lifecycle policy; remove it manually after reviewing before running the isolated acceptance suite." >&2
  exit 1
fi
mkdir -p .runtime
work="$(mktemp -d)"
api_pid="" gateway_pid=""
cleanup() {
  for pid in "$gateway_pid" "$api_pid"; do
    if test -n "$pid"; then kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; fi
  done
  rm -f .runtime/lifecycle.json
  rm -rf -- "$work"
  unset API_KEY ADMIN_KEY || true
}
trap cleanup EXIT INT TERM

export API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
export ADMIN_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"

python3 -m compileall -q tools consumers
for file in contracts/*.openapi.json examples/*.json; do python3 -m json.tool "$file" >/dev/null; done
python3 tools/contract_diff.py contracts/orderplacement-1.0.0.openapi.json contracts/orderplacement-1.1.0.openapi.json
set +e
python3 tools/contract_diff.py contracts/orderplacement-1.1.0.openapi.json contracts/orderplacement-2.0.0.openapi.json > "$work/breaking.log" 2>&1
result=$?
set -e
if test "$result" -ne 2; then cat "$work/breaking.log"; echo "Breaking change not rejected as expected" >&2; exit 1; fi
echo "PASS: incompatible schema has exit status 2"

dotnet build src/OrderPlacementApi/OrderPlacementApi.csproj -c Release
ASPNETCORE_URLS=http://127.0.0.1:8080 V1_LIFECYCLE=active ALLOWED_MAJOR=both \
  dotnet run --project src/OrderPlacementApi/OrderPlacementApi.csproj \
    -c Release --no-build --no-launch-profile > "$work/api.log" 2>&1 &
api_pid="$!"
for i in $(seq 1 30); do
  if python3 - <<'PY'
import urllib.request,sys
try:
    with urllib.request.urlopen("http://127.0.0.1:8080/healthz", timeout=1) as r:
        assert r.status == 200 and r.read() == b"ok"
except Exception:
    sys.exit(1)
PY
  then break; fi
  if test "$i" -eq 30; then cat "$work/api.log"; exit 1; fi
  sleep 1
done
python3 tools/check.py --base-url http://127.0.0.1:8080 --v1-status active

python3 tools/policy.py set active
python3 tools/gateway.py > "$work/gateway.log" 2>&1 &
gateway_pid="$!"
for i in $(seq 1 30); do
  if python3 - <<'PY'
import urllib.request,sys
try:
    with urllib.request.urlopen("http://127.0.0.1:8081/healthz", timeout=1) as r:
        assert r.status == 200 and r.read() == b"ok"
except Exception:
    sys.exit(1)
PY
  then break; fi
  if test "$i" -eq 30; then cat "$work/gateway.log"; exit 1; fi
  sleep 1
done
python3 tools/check.py --base-url http://127.0.0.1:8081 --v1-status active
python3 tools/policy.py set deprecated
python3 tools/check.py --base-url http://127.0.0.1:8081 --v1-status deprecated
python3 tools/policy.py set sunset
python3 tools/check.py --base-url http://127.0.0.1:8081 --v1-status sunset
python3 tools/policy.py set active
python3 tools/check.py --base-url http://127.0.0.1:8081 --v1-status active
python3 tools/metrics.py > "$work/metrics.log"
python3 - "$work/metrics.log" <<'PY'
import json,sys
doc=json.load(open(sys.argv[1]))
c=doc["counts"]
for k in ("v1_201", "v2_201", "v1_410", "v1_401", "v2_400"):
    assert c.get(k,0)>=1,(k,c)
assert doc["v1Policy"]=="active", doc
print("PASS: version-specific analytics + rollback")
PY
echo "PASS: Module 12 local acceptance suite"
