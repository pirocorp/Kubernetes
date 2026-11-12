"""Sanity check: all expected training source and config files are present."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
files = [
    "src/frontend/server.mjs", "src/frontend/public/index.html",
    "src/frontend/public/app.js", "src/frontend/Dockerfile",
    "src/backend/server.mjs", "src/backend/package.json", "src/backend/Dockerfile",
    "src/redirector/server.mjs", "src/redirector/package.json", "src/redirector/Dockerfile",
    "sql/init.sql", "compose.yaml", "openshift/frontend-route.yaml",
    "tools/init_env.py", "tools/prepare_oc.py",
    "tools/verify.py", "scripts/verify-node.sh", "scripts/verify-compose.sh"
]
missing = [name for name in files if not (root / name).is_file()]
if missing:
    raise SystemExit("Missing project files: " + ", ".join(missing))
print("PASS all", len(files), "required source, test and deployment files are included")
