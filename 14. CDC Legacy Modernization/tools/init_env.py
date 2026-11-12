"""Generate local random lab credentials; retain existing .env and never print secrets."""
from pathlib import Path
import os
import secrets
path = Path(__file__).resolve().parents[1] / ".env"
if path.exists():
    print("Existing .env retained unchanged")
else:
    data = "".join(f"{name}={secrets.token_hex(24)}\n"
                   for name in ("PG_PASSWORD", "CASHBACK_PASSWORD"))
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(data)
    print("Created .env with local random credentials and mode 0600")
