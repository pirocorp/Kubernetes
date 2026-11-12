#!/usr/bin/env bash
# No Docker/Node dependencies: verify frontend independently and syntax-check all services.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v node >/dev/null || { echo "Node.js >=22 required"; exit 1; }
command -v python3 >/dev/null || { echo "Python >=3.10 required"; exit 1; }
node -e 'if (Number(process.versions.node.split(".")[0]) < 22) process.exit(1)'
for file in src/frontend/server.mjs src/frontend/public/app.js src/backend/server.mjs src/redirector/server.mjs; do
  node --check "$file"
done
for file in src/frontend/package.json src/backend/package.json src/redirector/package.json; do
  python3 -m json.tool "$file" >/dev/null
done
python3 - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(("127.0.0.1",3110))
print("PASS port 3110 available")
PY
logs="$(mktemp)"
pid=""
cleanup() {
  if test -n "$pid"; then kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; fi
  rm -f -- "$logs"
}
trap cleanup EXIT
PORT=3110 BACKEND_URL=http://127.0.0.1:3111 REDIRECTOR_URL=http://127.0.0.1:3112 \
  node src/frontend/server.mjs > "$logs" 2>&1 &
pid="$!"
for i in $(seq 1 30); do
  if python3 - <<'PY'
import urllib.request,sys
try:
    with urllib.request.urlopen("http://127.0.0.1:3110/healthz",timeout=1) as r:
        assert r.status==200 and r.read()==b"ok"
except Exception: sys.exit(1)
PY
  then break; fi
  if test "$i" = 30; then cat "$logs"; exit 1; fi
  sleep 1
done
python3 - <<'PY'
import json
import urllib.request
import urllib.error
base="http://127.0.0.1:3110"
with urllib.request.urlopen(base + "/") as r:
    assert r.status==200 and b"Shorties" in r.read()
with urllib.request.urlopen(base + "/app.js") as r:
    assert r.status==200 and b"/api/shorten" in r.read()
with urllib.request.urlopen(base + "/api/status") as r:
    data=json.load(r)
    assert data["frontend"] and not data["backend"] and not data["database"] and not data["redirector"], data
req=urllib.request.Request(base+"/api/shorten", method="POST",
    data=b'{"url":"https://example.org"}',
    headers={"Content-Type":"application/json"})
try:
    urllib.request.urlopen(req,timeout=5)
except urllib.error.HTTPError as e:
    assert e.code==502,e.code
else:
    raise AssertionError("Disconnected backend was expected to return HTTP 502")
print("PASS standalone JS frontend, static assets, degraded status and explicit 502")
PY
echo "PASS Module 10 Node.js syntax and frontend smoke suite"
