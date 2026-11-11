"""Synthetic API consumer; tests migration between 1.0, 1.1 and 2.0."""
import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", choices=["1.0.0", "1.1.0", "2.0.0"], required=True)
    p.add_argument("--base-url", default="http://127.0.0.1:8081")
    args = p.parse_args()
    key = os.getenv("API_KEY", "")
    if len(key) < 16:
        raise SystemExit("Set API_KEY to at least 16 characters")
    data = (ROOT / "examples" / f"order-{args.version}.json").read_bytes()
    major = args.version.split(".")[0]
    path = f"/v{major}/placeorder"
    request = urllib.request.Request(
        args.base_url.rstrip("/") + path,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "X-Api-Key": key},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            code, body, headers = response.status, response.read(), response.headers
    except urllib.error.HTTPError as error:
        code, body, headers = error.code, error.read(), error.headers
    print("Client contract:", args.version, "Endpoint:", path)
    print("HTTP:", code, "API revision:", headers.get("X-API-Revision", "(none)"))
    for h in ("Deprecation", "Sunset"):
        if headers.get(h):
            print(h + ":", headers[h])
    try:
        print("Response:", json.loads(body))
    except ValueError:
        print("Non-JSON body")
    if code != 201:
        raise SystemExit(1)
