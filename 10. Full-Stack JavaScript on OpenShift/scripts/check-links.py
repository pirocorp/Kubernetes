"""Sanity check: all expected training source and config files are present."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
files = [
    "src/frontend/package.json", "src/frontend/package-lock.json",
    "src/frontend/server.mjs", "src/frontend/public/index.html",
    "src/frontend/public/app.js", "src/frontend/Dockerfile",
    "src/backend/server.mjs", "src/backend/package.json", "src/backend/package-lock.json", "src/backend/Dockerfile",
    "src/redirector/server.mjs", "src/redirector/package.json", "src/redirector/package-lock.json", "src/redirector/Dockerfile",
    "sql/init.sql", "compose.yaml", "openshift/frontend-route.yaml",
    "tools/init_env.py", "tools/prepare_oc.py",
    "tools/verify.py", "tools/verify_cluster.py", "scripts/verify-node.sh", "scripts/verify-compose.sh"
]
missing = [name for name in files if not (root / name).is_file()]
if missing:
    raise SystemExit("Missing project files: " + ", ".join(missing))
for service in ("frontend", "backend", "redirector"):
    package = json.loads((root / "src" / service / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((root / "src" / service / "package-lock.json").read_text(encoding="utf-8"))
    assert lock["lockfileVersion"] >= 3, f"Unsupported lockfile version: {service}"
    assert lock["name"] == package["name"], f"Package name differs: {service}"
    assert lock["version"] == package["version"], f"Package version differs: {service}"
    assert lock["packages"][""].get("dependencies", {}) == package.get("dependencies", {}), f"Dependency lock differs: {service}"
print("PASS all", len(files), "required files and consistent npm lock manifests")
