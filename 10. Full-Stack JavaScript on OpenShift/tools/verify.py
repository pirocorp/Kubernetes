"""End-to-end tests for URL Shortener with real PostgreSQL + Node services."""
import json
import re
import subprocess
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:3110"
BACK = "http://127.0.0.1:3111"
REDIRECT = "http://127.0.0.1:3112"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

client = urllib.request.build_opener(NoRedirect)

def request(method, base, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        base + path, method=method, data=body,
        headers={"content-type": "application/json"} if body else {})
    try:
        with client.open(req, timeout=6) as res:
            return res.status, res.read(), res.headers
    except urllib.error.HTTPError as err:
        return err.code, err.read(), err.headers

def ready():
    for base in (BASE, BACK, REDIRECT):
        code, raw, _ = request("GET", base, "/healthz")
        if code != 200 or raw != b"ok":
            return False
    data = json.loads(request("GET", BASE, "/api/status")[1])
    return all(data.values())

def wait_ready(seconds=75):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        try:
            if ready():
                return
        except (OSError, ValueError, KeyError, TimeoutError):
            pass
        time.sleep(1)
    raise SystemExit("TIMEOUT: frontend/backend/redirector/Postgres readiness")

wait_ready()
print("PASS all services healthy and DB-backed readiness")

code, html, _ = request("GET", BASE, "/")
assert code == 200 and b"Shorties" in html and b"app.js" in html
code, js, _ = request("GET", BASE, "/app.js")
assert code == 200 and b"Shorten URL" not in js and b"/api/shorten" in js
print("PASS real browser frontend and JavaScript assets")

bad, _, _ = request("POST", BASE, "/api/shorten", {"url": "ftp://invalid.example"})
assert bad == 400, bad
bad, _, _ = request("POST", BASE, "/api/shorten", {"url": "https://name:password@example.com/"})
assert bad == 400, bad
print("PASS rejected invalid and credential-embedded URLs")

url = "https://example.org/learning/full-stack-js?step=5"
status, data, _ = request("POST", BASE, "/api/shorten", {"url": url})
assert status == 201, (status, data)
payload = json.loads(data)
short_code = payload["code"]
assert re.fullmatch(r"[A-Za-z0-9_-]{7,12}", short_code), payload
assert payload["path"] == "/r/" + short_code
print("PASS PostgreSQL-backed short URL created", short_code)

status, _, headers = request("GET", BASE, "/r/" + short_code)
assert status == 302 and headers.get("Location") == url, (status, headers)
status, _, headers = request("GET", REDIRECT, "/r/" + short_code)
assert status == 302 and headers.get("Location") == url, (status, headers)
missing, _, _ = request("GET", BASE, "/r/unknown")
assert missing == 404, missing
print("PASS frontend + direct redirector HTTP 302 and unknown-code 404")

subprocess.run(["docker", "compose", "restart", "frontend", "backend", "redirector"],
               check=True, stdout=subprocess.DEVNULL)
wait_ready()
status, _, headers = request("GET", BASE, "/r/" + short_code)
assert status == 302 and headers.get("Location") == url, (status, headers)
print("PASS short URL survives application restart (actual PostgreSQL persistence)")

result = subprocess.run(
    ["docker", "compose", "exec", "-T", "database", "psql",
     "-U", "shorties", "-d", "shorties", "-Atc",
     "SELECT COUNT(*) FROM short_links WHERE code='" + short_code + "'"],
    capture_output=True, text=True, check=True)
assert result.stdout.strip() == "1", result.stdout
print("PASS SQL row persisted exactly once")
print("ALL MODULE 10 REAL FULL-STACK INTEGRATION CHECKS PASSED")
