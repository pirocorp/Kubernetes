"""Demo inference HTTP endpoint; deterministic fixture, NOT a trained ML model."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/predict":
            self.send_error(404)
            return
        # .NET JsonContent may use HTTP/1.1 Transfer-Encoding: chunked.
        # Python's BaseHTTPRequestHandler does not automatically decode it.
        # This is a bounded, explicit decoder for this LOCAL fixture.
        try:
            if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
                chunks = []
                total = 0
                while True:
                    line = self.rfile.readline(64).strip()
                    size = int(line.split(b";", 1)[0], 16)
                    if size < 0 or total + size > 2048:
                        raise ValueError("Request body too large")
                    if size == 0:
                        # Consume trailers, if any, through the terminating blank line.
                        while self.rfile.readline(1024).strip():
                            pass
                        break
                    chunk = self.rfile.read(size)
                    if len(chunk) != size or self.rfile.read(2) != b"\r\n":
                        raise ValueError("Malformed chunk encoding")
                    chunks.append(chunk)
                    total += size
                raw_body = b"".join(chunks)
            else:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 2048:
                    raise ValueError("Request body too large or missing")
                raw_body = self.rfile.read(length)
                if len(raw_body) != length:
                    raise ValueError("Incomplete request body")
            if not raw_body:
                raise ValueError("Empty body")
        except (ValueError, OverflowError):
            self.send_error(413)
            return
        try:
            body = json.loads(raw_body)
            raw = body["text"]
            if not isinstance(raw, str):
                raise ValueError()
            text = raw.lower()
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
