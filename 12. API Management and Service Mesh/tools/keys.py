"""Generate local, non-production training credentials. Never prints secret values."""
import os
import secrets
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime"
KEYS = RUNTIME / "keys.env"
NAMES = ("PARTNER_RED_KEY", "PARTNER_BLUE_KEY", "ADMIN_KEY")


def bootstrap():
    RUNTIME.mkdir(mode=0o700, exist_ok=True)
    if KEYS.exists():
        os.chmod(KEYS, 0o600)
        print("Existing local credentials retained: .runtime/keys.env")
        return
    lines = [name + "=" + secrets.token_hex(24) for name in NAMES]
    fd = os.open(KEYS, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("Created .runtime/keys.env (mode 0600, values not printed)")


def check_ports():
    for port in (5100, 5101, 5102, 5200, 5300):
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError as e:
                raise SystemExit(f"Local TCP port {port} unavailable: {e}")
    print("Local ports 5100, 5101, 5102, 5200, 5300 available")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("bootstrap", "check-ports"):
        raise SystemExit("Usage: python3 tools/keys.py bootstrap|check-ports")
    {"bootstrap": bootstrap, "check-ports": check_ports}[sys.argv[1]]()
