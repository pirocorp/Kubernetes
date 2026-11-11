"""LOCAL educational north-south API management proxy, NOT Red Hat 3scale.

Partner authentication, simple rolling-window limits and per-partner counts.
This demo has no TLS, developer portal, billing, OIDC or persistent analytics.
"""
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RED = os.getenv("PARTNER_RED_KEY", "")
BLUE = os.getenv("PARTNER_BLUE_KEY", "")
ADMIN = os.getenv("ADMIN_KEY", "")
UPSTREAM = os.getenv("AGENCY_V2_URL", "http://127.0.0.1:5102").rstrip("/")
if min(map(len, (RED, BLUE, ADMIN))) < 16:
    raise SystemExit("PARTNER_RED_KEY, PARTNER_BLUE_KEY, ADMIN_KEY must be set (>=16 chars)")
LIMITS = {"red": 3, "blue": 6}
WINDOW = 15
windows = defaultdict(deque)
metrics = Counter()


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload, media="application/json"):
        data = json.dumps(payload).encode() if not isinstance(payload, bytes) else payload
        self.send_response(status)
        self.send_header("Content-Type", media)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/healthz":
            return self.reply(200, b"ok", "text/plain")
        if self.path == "/_metrics":
            if not hmac.compare_digest(self.headers.get("X-Admin-Key", ""), ADMIN):
                return self.reply(401, {"code": "unauthorized", "message": "Admin key required"})
            return self.reply(200, {"counts": dict(metrics), "limits": LIMITS, "windowSeconds": WINDOW})
        if not self.path.startswith("/partner/travels/"):
            return self.reply(404, {"code": "not_found", "message": "Unknown path"})
        supplied = self.headers.get("X-Partner-Key", "")
        partner = "red" if hmac.compare_digest(supplied, RED) else (
            "blue" if hmac.compare_digest(supplied, BLUE) else None
        )
        if partner is None:
            metrics["denied_401"] += 1
            return self.reply(401, {"code": "unauthorized", "message": "Invalid partner key"})
        window = windows[partner]
        now = time.monotonic()
        while window and now - window[0] >= WINDOW:
            window.popleft()
        if len(window) >= LIMITS[partner]:
            metrics["limited_" + partner] += 1
            return self.reply(429, {"code": "rate_limited", "message": "Partner quota exceeded"})
        window.append(now)
        path = "/api/travels/" + self.path[len("/partner/travels/"):]
        req = urllib.request.Request(UPSTREAM + path)
        try:
            with urllib.request.urlopen(req, timeout=4) as response:
                status, body = response.status, response.read()
        except urllib.error.HTTPError as error:
            status, body = error.code, error.read()
        except (urllib.error.URLError, TimeoutError):
            metrics["upstream_502"] += 1
            return self.reply(502, {"code": "bad_gateway", "message": "Travel agency unavailable"})
        metrics["requests_" + partner] += 1
        return self.reply(status, body)


if __name__ == "__main__":
    bind = os.getenv("GATEWAY_BIND", "127.0.0.1")
    port = int(os.getenv("GATEWAY_PORT", "5300"))
    print(f"Teaching-only partner gateway http://{bind}:{port}", flush=True)
    ThreadingHTTPServer((bind, port), Handler).serve_forever()
