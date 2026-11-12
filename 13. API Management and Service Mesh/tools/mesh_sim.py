"""LOCAL educational HTTP routing simulator, NOT an Istio/Envoy service mesh.

80/20 deterministic split, one retry on 503/connection failure for GET only.
No mTLS, proxy injection, Kubernetes policy, tracing backend or real mesh.
"""
import json
import os
import urllib.error
import urllib.request
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

V1 = os.getenv("V1_URL", "http://127.0.0.1:5101").rstrip("/")
V2 = os.getenv("V2_URL", "http://127.0.0.1:5102").rstrip("/")
counts = Counter()
sequence = 0


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload, media="application/json"):
        data = json.dumps(payload).encode() if not isinstance(payload, bytes) else payload
        self.send_response(status)
        self.send_header("Content-Type", media)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        global sequence
        if self.path == "/healthz":
            return self.reply(200, b"ok", "text/plain")
        if self.path == "/_stats":
            return self.reply(200, dict(counts))
        if not self.path.startswith("/api/travels/"):
            return self.reply(404, {"code": "not_found", "message": "Unknown route"})
        sequence += 1
        # Every fifth request goes first to v2: exactly 80/20 for a multiple of 5.
        chosen = "v2" if sequence % 5 == 0 else "v1"
        counts["selected_" + chosen] += 1
        for attempt, target in enumerate([chosen, "v1"] if chosen == "v2" else [chosen]):
            url = V2 if target == "v2" else V1
            headers = {}
            if "X-Correlation-Id" in self.headers:
                headers["X-Correlation-Id"] = self.headers["X-Correlation-Id"][:64]
            req = urllib.request.Request(url + self.path, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=3) as response:
                    status, data = response.status, response.read()
            except urllib.error.HTTPError as error:
                status, data = error.code, error.read()
            except (urllib.error.URLError, TimeoutError):
                status, data = 503, json.dumps(
                    {"code": "unavailable", "message": "Local upstream unavailable"}
                ).encode()
            if attempt == 0 and target == "v2" and status == 503:
                counts["retry_to_v1"] += 1
                continue
            counts["result_" + target] += 1
            # Pass the upstream's actual JSON response without inventing values.
            return self.reply(status, data)
        self.reply(502, {"code": "bad_gateway", "message": "No upstream succeeded"})


if __name__ == "__main__":
    print("Teaching-only traffic router http://127.0.0.1:5200", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 5200), Handler).serve_forever()
