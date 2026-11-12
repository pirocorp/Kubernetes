"""Generate a random local-only Postgres password, preserving existing state."""
import os
import secrets
from pathlib import Path
file = Path(__file__).resolve().parents[1] / ".env"
if file.exists():
    print("Retaining existing .env (credentials not overwritten)")
else:
    data = "M10_DB_PASSWORD=" + secrets.token_hex(24) + "\n"
    fd = os.open(file, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as target:
        target.write(data)
    print("Created .env with 0600 permissions; credentials not printed")
