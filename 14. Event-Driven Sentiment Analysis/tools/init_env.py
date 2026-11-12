"""Generate local-only Docker Compose credentials without printing secret values."""
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / ".env"
VALUES = ("PG_PASSWORD", "INFLUX_PASSWORD", "INFLUX_TOKEN", "GRAFANA_PASSWORD")

if FILE.exists():
    print("Retaining the existing .env; no credentials overwritten")
else:
    data = "\n".join(name + "=" + secrets.token_hex(24) for name in VALUES) + "\n"
    fd = os.open(FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(data)
    print("Created local .env with random credentials (mode 0600); values not printed")
