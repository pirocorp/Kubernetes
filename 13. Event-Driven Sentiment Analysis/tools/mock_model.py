"""Demo inference HTTP endpoint; deterministic fixture, NOT a trained ML model."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/predict":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 2048:
            self.send_error(413)
            return
        try:
            body = json.loads(self.rfile.read(length))
            text = body["text"].lower()
            if not isinstance(text, str):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            self.send_error(400)
            return
        label = "positive" if "great" in text or "love" in text else (
            "negative" if "broken" in text or "terrible" in text else "neutral")
        score = 0.9 if label == "positive" else -0.9 if label == "negative" else 0.0
        data = json.dumps({"label": label, "score": score, "model": "python-fixture-NOT-ML"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    print("Local deterministic model fixture: http://127.0.0.1:8090/predict")
    ThreadingHTTPServer(("127.0.0.1", 8090), Handler).serve_forever()
