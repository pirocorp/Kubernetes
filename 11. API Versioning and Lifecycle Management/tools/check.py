"""End-to-end HTTP checks for both ASP.NET Core and local gateway (Python stdlib)."""
import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def request(base, path, payload, key=None):
    headers = {"Content-Type": "application/json"}
    if key is not None:
        headers["X-Api-Key"] = key
    req = urllib.request.Request(base.rstrip("/") + path, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            return res.status, json.loads(res.read()), res.headers
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read()), error.headers


def expect(base, path, payload, key, status, expected_rev=None):
    code, result, headers = request(base, path, payload, key)
    assert code == status, f"{path}: expected HTTP {status}, got {code}: {result}"
    if status == 201:
        assert result["status"] == "accepted" and result["orderId"].startswith("ord-"), result
        assert headers.get("X-API-Revision") == expected_rev, headers
    elif status in (400, 401, 410):
        assert isinstance(result.get("code"), str) and isinstance(result.get("message"), str), result
    print(f"PASS {path} => {status}")
    return headers


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default="http://127.0.0.1:8080")
    ap.add_argument("--v1-status", choices=["active", "deprecated", "sunset"], default="active")
    args = ap.parse_args()
    key = os.getenv("API_KEY", "")
    if len(key) < 16:
        raise SystemExit("Set API_KEY to at least 16 characters")
    base = args.base_url
    v10 = json.loads((ROOT / "examples/order-1.0.0.json").read_text())
    v11 = json.loads((ROOT / "examples/order-1.1.0.json").read_text())
    v20 = json.loads((ROOT / "examples/order-2.0.0.json").read_text())
    expect(base, "/v1/placeorder", v10, None, 401)
    old_status = 410 if args.v1_status == "sunset" else 201
    first = expect(base, "/v1/placeorder", v10, key, old_status, "1.1.0" if old_status == 201 else None)
    if args.v1_status != "active":
        assert first.get("Deprecation") and first.get("Sunset"), "Missing RFC lifecycle headers"
        print("PASS v1 lifecycle headers")
    expect(base, "/v1/placeorder", v11, key, old_status, "1.1.0" if old_status == 201 else None)
    expect(base, "/v2/placeorder", v20, key, 201, "2.0.0")
    expect(base, "/v2/placeorder", v10, key, 400)
    expect(base, "/v1/placeorder", v20, key, 410 if old_status == 410 else 400)
    print("ALL VERSION COMPATIBILITY CHECKS PASSED")
