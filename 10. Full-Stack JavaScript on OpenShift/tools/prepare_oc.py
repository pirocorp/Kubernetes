"""Generate OpenShift template parameters + Secret input from local random credentials."""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".env"
if not SOURCE.exists():
    raise SystemExit("Run python3 tools/init_env.py first")
text = SOURCE.read_text(encoding="utf-8")
match = re.search(r"^M10_DB_PASSWORD=([a-f0-9]{48})$", text, re.MULTILINE)
if not match:
    raise SystemExit(".env does not contain expected generated M10_DB_PASSWORD")
password = match.group(1)
directory = ROOT / ".runtime"
directory.mkdir(exist_ok=True)
documents = {
    "postgres.params": "DATABASE_SERVICE_NAME=m10-postgres\nPOSTGRESQL_USER=shorties\n"
                       "POSTGRESQL_DATABASE=shorties\nPOSTGRESQL_PASSWORD=" + password + "\n",
    "database.env": "DATABASE_URL=postgresql://shorties:" + password +
                    "@m10-postgres:5432/shorties\n",
}
for name, value in documents.items():
    path = directory / name
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write(value)
    os.chmod(path, 0o600)
print("Prepared .runtime/postgres.params and .runtime/database.env (0600; no secrets printed)")
