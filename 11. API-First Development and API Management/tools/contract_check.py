"""Small contract-driven HTTP smoke suite, Python 3.10+ standard library.

Checks a practical subset of JSON Schema (types, required fields and enums).
Not a replacement for full OpenAPI validators, Dredd, Schemathesis, etc.
"""
import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "contract/products-v1.openapi.json").read_text())


def shape(schema, obj, trail="$"):
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        return shape(CONTRACT["components"]["schemas"][name], obj, trail)
    typ = schema.get("type")
    matches = {
        "object": isinstance(obj, dict),
        "array": isinstance(obj, list),
        "string": isinstance(obj, str),
        "number": type(obj) in (int, float),
        "integer": type(obj) is int,
        "boolean": type(obj) is bool,
    }
    if typ in matches and not matches[typ]:
        raise AssertionError(f"{trail}: expected {typ}; received {type(obj).__name__}")
    if "enum" in schema and obj not in schema["enum"]:
        raise AssertionError(f"{trail}: invalid enum value {obj}")
    if isinstance(obj, dict):
        if schema.get("additionalProperties") is False:
            extra = set(obj) - set(schema.get("properties", {}))
            if extra:
                raise AssertionError(f"{trail}: additional properties are not permitted: {sorted(extra)}")
        for name in schema.get("required", []):
            if name not in obj:
                raise AssertionError(f"{trail}: missing {name}")
        for key, value in obj.items():
            if key in schema.get("properties", {}):
                shape(schema["properties"][key], value, f"{trail}.{key}")
    if isinstance(obj, list):
        for index, value in enumerate(obj):
            shape(schema.get("items", {}), value, f"{trail}[{index}]")


def request(base, method, path, key=None, payload=None):
    raw = json.dumps(payload).encode() if payload is not None else None
    headers = {}
    if key is not None:
        headers["X-Api-Key"] = key
    if raw is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=raw, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            return res.status, res.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def expect(base, method, path, status, schema=None, key=None, payload=None):
    got, text = request(base, method, path, key, payload)
    if got != status:
        raise AssertionError(f"{method} {path}: expected {status}, got {got}: {text}")
    if schema is not None:
        parsed = json.loads(text)
        shape({"$ref": "#/components/schemas/" + schema}, parsed)
    print("PASS", method, path, "=>", status)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    args = p.parse_args()
    key = os.getenv("API_KEY")
    if not key or len(key) < 16:
        raise SystemExit("Set API_KEY to a secret >=16 characters")
    base = args.base_url.rstrip("/")
    status, body = request(base, "GET", "/healthz")
    assert status == 200 and body.strip() == "ok", (status, body)
    print("PASS GET /healthz => 200")
    expect(base, "GET", "/v1/products", 401, "ApiError")
    expect(base, "GET", "/v1/products", 200, "ProductList", key)
    expect(base, "GET", "/v1/products/p-100", 200, "Product", key)
    expect(base, "GET", "/v1/products/not-present", 404, "ApiError", key)
    expect(
        base, "POST", "/v1/products", 201, "Product", key,
        {"name": "Monitor", "price": 129, "currency": "EUR"}
    )
    expect(
        base, "POST", "/v1/products", 400, "ApiError", key,
        {"name": "Bad item", "currency": "EUR"}  # missing required price
    )
    expect(
        base, "POST", "/v1/products", 400, "ApiError", key,
        {"name": "", "price": -1, "currency": "EUR"}
    )
    expect(
        base, "POST", "/v1/products", 400, "ApiError", key,
        {"name": "Extra field test", "price": 15, "currency": "EUR", "unexpected": True}
    )
    print("Contract smoke tests PASSED (required fields, subset of types and closed schemas).")


if __name__ == "__main__":
    main()
