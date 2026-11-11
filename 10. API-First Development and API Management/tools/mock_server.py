"""OpenAPI example-driven mock server; Python 3.10+ standard library only."""
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

CONTRACT = json.loads(
    (Path(__file__).resolve().parents[1] / "contract/products-v1.openapi.json").read_text()
)
API_KEY = os.environ.get("API_KEY", "")
if len(API_KEY) < 16:
    raise SystemExit("Set API_KEY to at least 16 characters.")


class Handler(BaseHTTPRequestHandler):
    def respond(self, code, body, media="application/json"):
        raw = (json.dumps(body) if media == "application/json" else str(body)).encode()
        self.send_response(code)
        self.send_header("Content-Type", media)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def example(self, path, method, status):
        return CONTRACT["paths"][path][method]["responses"][str(status)]["content"][
            "application/json"
        ]["example"]

    def authorized(self):
        if hmac.compare_digest(self.headers.get("X-Api-Key", ""), API_KEY):
            return True
        self.respond(401, self.example("/v1/products", "get", 401))
        return False

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/healthz":
            self.respond(200, "ok", "text/plain")
        elif not self.authorized():
            return
        elif path == "/v1/products":
            self.respond(200, self.example(path, "get", 200))
        elif path == "/v1/products/p-100":
            self.respond(200, self.example("/v1/products/{id}", "get", 200))
        elif path.startswith("/v1/products/"):
            self.respond(404, self.example("/v1/products/{id}", "get", 404))
        else:
            self.respond(404, {"code": "not_found", "message": "Unknown path"})

    def do_POST(self):
        if not self.authorized():
            return
        if self.path != "/v1/products":
            self.respond(404, {"code": "not_found", "message": "Unknown path"})
            return
        # The mock responds with an OpenAPI example and does NOT persist changes.
        length = int(self.headers.get("Content-Length", "0"))
        if length > 16384:
            self.respond(413, {"code": "validation_error", "message": "Body too large"})
            return
        try:
            body = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            return self.respond(400, self.example("/v1/products", "post", 400))
        required = CONTRACT["components"]["schemas"]["NewProduct"]["required"]
        valid = (
            isinstance(body, dict)
            and all(field in body for field in required)
            and isinstance(body.get("name"), str)
            and bool(body["name"].strip())
            and len(body["name"]) <= 100
            and set(body) <= set(CONTRACT["components"]["schemas"]["NewProduct"]["properties"])
            and type(body.get("price")) in (int, float)
            and body["price"] >= 0
            and body.get("currency") == "EUR"
        )
        if not valid:
            return self.respond(400, self.example("/v1/products", "post", 400))
        self.respond(201, self.example("/v1/products", "post", 201))


if __name__ == "__main__":
    print("Contract-driven mock: http://127.0.0.1:8082 (not a real API)")
    HTTPServer(("127.0.0.1", 8082), Handler).serve_forever()
