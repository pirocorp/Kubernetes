#!/usr/bin/env bash
# Stop only lab-owned processes, checked against the expected command lines.
set -euo pipefail
cd "$(dirname "$0")/.."
for name in gateway router portal agency-v2 agency-v1; do
  file=".runtime/$name.pid"
  if ! test -f "$file"; then continue; fi
  pid="$(cat "$file")"
  if ! [[ "$pid" =~ ^[0-9]+$ ]]; then
    echo "Invalid PID in $file. Inspect manually." >&2
    continue
  fi
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f -- "$file"
    echo "Removed stale PID for $name (process no longer running)"
    continue
  fi
  args="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  case "$name:$args" in
    gateway:*tools/partner_gateway.py*|router:*tools/mesh_sim.py*|portal:*Travelz.dll*|agency-v1:*Travelz.dll*|agency-v2:*Travelz.dll*)
      kill "$pid" 2>/dev/null || true
      rm -f -- "$file"
      echo "Stopped $name"
      ;;
    *)
      echo "PID $pid is not the expected $name process; NOT killing it." >&2
      ;;
  esac
done
echo "Local keys and log files are retained under .runtime/ for review."
