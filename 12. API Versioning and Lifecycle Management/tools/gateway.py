"""Local training gateway: per-version request counters, lifecycle, key checks.

NOT 3scale, APIcast or production middleware: local process, in-memory counters,
no distributed identity, no TLS, no HA, no persistent analytics or portal.
"""
import hmac
import json
import os
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / ".runtime" / "lifecycle.json"
API_KEY = os.getenv("API_KEY", "")
ADMIN_KEY = os.getenv("ADMIN_KEY", "")
UPSTREAM = os.getenv("M11_API_URL", "http://127.0.0.1:8080").rstrip("/")
if min(len(API_KEY), len(ADMIN_KEY)) < 16:
    raise SystemExit("Set API_KEY and ADMIN_KEY with at least 16 characters")
stats = Counter()
DEPRECATION_DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)
SUNSET_DATE = datetime(2027, 6, 30, tzinfo=timezone.utc)


def state():
    try:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        value = policy["v1"]
        if value not in ("active", "deprecated", "sunset"):
            raise ValueError("bad state")
        return value
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        return None


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, headers=None, media="application/json"):
        data = json.dumps(body).encode() if not isinstance(body, bytes) else body
        self.send_response(status)
        self.send_header("Content-Type", media)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/healthz":
            self.reply(200, b"ok", media="text/plain")
            return
        if self.path == "/_metrics":
            if not hmac.compare_digest(self.headers.get("X-Admin-Key", ""), ADMIN_KEY):
                self.reply(401, {"code": "unauthorized", "message": "Admin key required"})
                return
            self.reply(200, {"counts": dict(stats), "v1Policy": state()})
            return
        self.reply(404, {"code": "not_found", "message": "No such endpoint"})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path not in ("/v1/placeorder", "/v2/placeorder"):
            return self.reply(404, {"code": "not_found", "message": "No such endpoint"})
        version = "v1" if path.startswith("/v1/") else "v2"
        supplied = self.headers.get("X-Api-Key", "")
        if not hmac.compare_digest(supplied, API_KEY):
            stats[version + "_401"] += 1
            return self.reply(401, {"code": "unauthorized", "message": "Invalid API key"})
        current = state()
        if current is None:
            return self.reply(503, {"code": "misconfigured", "message": "Missing lifecycle policy"})
        headers = {}
        if version == "v1" and current in ("deprecated", "sunset"):
            headers = {
                "Deprecation": "@" + str(int(DEPRECATION_DATE.timestamp())),
                "Sunset": format_datetime(SUNSET_DATE, usegmt=True),
            }
        if version == "v1" and current == "sunset":
            stats["v1_410"] += 1
            return self.reply(410, {"code": "gone", "message": "Version v1 has been retired"}, headers)
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.reply(400, {"code": "validation_error", "message": "Invalid length"})
        if length <= 0 or length > 8192:
            return self.reply(413, {"code": "validation_error", "message": "Invalid body size"})
        data = self.rfile.read(length)
        req = urllib.request.Request(
            UPSTREAM + path,
            data=data,
            headers={"Content-Type": "application/json", "X-Api-Key": API_KEY},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=6) as response:
                status, body = response.status, response.read()
                revision = response.headers.get("X-API-Revision")
        except urllib.error.HTTPError as error:
            status, body = error.code, error.read()
            revision = error.headers.get("X-API-Revision")
        except (urllib.error.URLError, TimeoutError):
            stats[version + "_502"] += 1
            return self.reply(502, {"code": "bad_gateway", "message": "Backend unavailable"}, headers)
        if revision:
            headers["X-API-Revision"] = revision
        stats[version + "_" + str(status)] += 1
        self.reply(status, body, headers)

if __name__ == "__main__":
    print("Local versioning gateway on http://127.0.0.1:8081", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8081), Handler).serve_forever()
