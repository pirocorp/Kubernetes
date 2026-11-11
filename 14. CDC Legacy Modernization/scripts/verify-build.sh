#!/usr/bin/env bash
# Fast preflight without Kafka/Elasticsearch/Docker.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v dotnet >/dev/null || { echo ".NET 10 SDK missing" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Python 3.10+ missing" >&2; exit 1; }
test "$(dotnet --version | cut -d. -f1)" = "10" || {
  echo ".NET SDK 10 required" >&2; exit 1;
}
python3 -m compileall -q tools
dotnet build src/RetailModernization/RetailModernization.csproj -c Release
echo "PASS Module 14 C# and Python build"
