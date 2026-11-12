"""Tiny LOCAL teaching proxy for API-key access, limits and counters.

NOT Red Hat 3scale and NOT production-ready: in-memory counters, no HA/TLS,
single process, no developer portal, billing or identity federation.
"""
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict, deque
from http.server import BaseHTTPRequestHandler, HTTPServer

API_KEY = os.environ.get("API_KEY", "")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
UPSTREAM = os.environ.get("API_UPSTREAM", "http://127.0.0.1:8080")
if min(len(API_KEY), len(ADMIN_KEY)) < 16:
    raise SystemExit("Set both API_KEY and ADMIN_KEY (>=16 characters).")
WINDOW_SECONDS = 15
MAX_REQUESTS = 3
calls = defaultdict(deque)
metrics = Counter()


class Handler(BaseHTTPRequestHandler):
    def send_body(self, status, body, media="application/json"):
        content = json.dumps(body).encode() if isinstance(body, dict) else body
        if isinstance(content, str):
            content = content.encode()
        self.send_response(status)
        self.send_header("Content-Type", media)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def process(self, method):
        if self.path == "/_metrics":
            if not hmac.compare_digest(self.headers.get("X-Admin-Key", ""), ADMIN_KEY):
                return self.send_body(401, {"code": "unauthorized", "message": "Admin key required"})
            return self.send_body(200, dict(metrics))
        supplied = self.headers.get("X-Api-Key", "")
        if not hmac.compare_digest(supplied, API_KEY):
            metrics["denied"] += 1
            return self.send_body(401, {"code": "unauthorized", "message": "Invalid API key"})
        now = time.monotonic()
        window = calls[supplied]
        while window and now - window[0] >= WINDOW_SECONDS:
            window.popleft()
        if len(window) >= MAX_REQUESTS:
            metrics["limited"] += 1
            return self.send_body(429, {"code": "rate_limited", "message": "Too many requests"})
        window.append(now)
        size = int(self.headers.get("Content-Length", "0"))
        if size > 16384:
            return self.send_body(413, {"code": "validation_error", "message": "Body too large"})
        payload = self.rfile.read(size) if size else None
        req = urllib.request.Request(
            UPSTREAM + self.path,
            data=payload,
            headers={"X-Api-Key": API_KEY, "Content-Type": self.headers.get("Content-Type", "application/json")},
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as res:
                status, content, media = res.status, res.read(), res.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as ex:
            status, content, media = ex.code, ex.read(), ex.headers.get("Content-Type", "application/json")
        except (urllib.error.URLError, TimeoutError):
            metrics["upstream_errors"] += 1
            return self.send_body(502, {"code": "bad_gateway", "message": "Upstream unavailable"})
        metrics["requests"] += 1
        return self.send_body(status, content, media)

    def do_GET(self):
        self.process("GET")

    def do_POST(self):
        self.process("POST")


if __name__ == "__main__":
    print("Local teaching gateway: http://127.0.0.1:8081")
    HTTPServer(("127.0.0.1", 8081), Handler).serve_forever()
