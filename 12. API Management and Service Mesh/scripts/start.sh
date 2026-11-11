#!/usr/bin/env bash
# Start all five LOCAL training processes; WSL/Ubuntu/macOS Bash.
set -euo pipefail
cd "$(dirname "$0")/.."
for f in .runtime/*.pid; do
  if test -f "$f"; then
    echo "Found PID file: $f. Run bash scripts/stop.sh, verify, then retry." >&2
    exit 1
  fi
done
python3 tools/keys.py check-ports
python3 tools/keys.py bootstrap
set -a
# Created locally by tools/keys.py; do not source untrusted files.
. .runtime/keys.env
set +a
dotnet build src/Travelz/Travelz.csproj -c Release
DLL="src/Travelz/bin/Release/net10.0/Travelz.dll"
test -s "$DLL"

start_dotnet() {
  local name="$1" mode="$2" port="$3"
  APP_MODE="$mode" ASPNETCORE_URLS="http://127.0.0.1:$port" \
    AGENCY_URL="http://127.0.0.1:5200" \
    dotnet "$DLL" > ".runtime/$name.log" 2>&1 &
  printf '%s\n' "$!" > ".runtime/$name.pid"
}
start_dotnet agency-v1 agency-v1 5101
start_dotnet agency-v2 agency-v2 5102
start_dotnet portal portal 5100
python3 tools/mesh_sim.py > .runtime/router.log 2>&1 &
printf '%s\n' "$!" > .runtime/router.pid
python3 tools/partner_gateway.py > .runtime/gateway.log 2>&1 &
printf '%s\n' "$!" > .runtime/gateway.pid
sleep 2
if ! python3 tools/verify.py basic; then
  echo "Startup validation failed. Check .runtime/*.log and stop the lab." >&2
  exit 1
fi
echo "Travelz local lab ready: portal :5100, agency :5101/:5102, router :5200, gateway :5300."
echo "For further tests: set -a; source .runtime/keys.env; set +a"
