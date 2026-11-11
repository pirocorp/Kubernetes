"""End-to-end CDC acceptance through HTTP only; no direct source DB reads by modern API."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

LEGACY = "http://127.0.0.1:5084"
MODERN = "http://127.0.0.1:5085"

def request(base, method, path, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        base + path, method=method, data=body,
        headers={"Content-Type": "application/json"} if body else {})
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read().decode()
        return error.code, json.loads(raw) if raw else None

def wait_for(description, fetch, predicate, seconds=100):
    deadline = time.monotonic() + seconds
    last = None
    while time.monotonic() < deadline:
        try:
            last = fetch()
            if predicate(last):
                print("PASS", description)
                return last
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError):
            pass
        time.sleep(1)
    raise SystemExit(f"TIMEOUT {description}. Last observed: {last!r}")

def search(q):
    code, data = request(MODERN, "GET", "/search?q=" + urllib.parse.quote(q))
    return data if code == 200 else []

def wallet(id):
    code, data = request(MODERN, "GET", f"/wallets/{id}")
    return data if code == 200 else None

def expense(id):
    code, data = request(MODERN, "GET", f"/expenses/{id}")
    return data if code == 200 else None

def main():
    for base in [LEGACY, MODERN]:
        wait_for(f"HTTP health {base}",
                 lambda: request(base, "GET", "/healthz"),
                 lambda r: r == (200, None) or r[0] == 200, 90)
    code, items = request(LEGACY, "GET", "/legacy/products")
    assert code == 200 and {101, 102}.issubset({p["productId"] for p in items})
    print("PASS original legacy catalog")
    wait_for("initial Debezium product snapshot -> Elasticsearch",
             lambda: search("fern"),
             lambda items: any(p["productId"] == 101 for p in items))
    wait_for("initial customer snapshot -> new cashback database",
             lambda: wallet(1), lambda d: d is not None and d["tier"] == "bronze")

    new = {"productId": 7777, "name": "Purple Orchid", "description": "Rare indoor orchid",
           "priceCents": 2500}
    code, _ = request(LEGACY, "POST", "/legacy/products", new)
    assert code == 201, code
    wait_for("new product auto-indexed by CDC",
             lambda: search("orchid"),
             lambda items: any(p["productId"] == 7777 for p in items))
    updated = {**new, "name": "Purple Orchid Deluxe", "priceCents": 3100}
    code, _ = request(LEGACY, "PUT", "/legacy/products/7777", updated)
    assert code == 200, code
    wait_for("product update reflected without dual-write",
             lambda: search("orchid"),
             lambda items: any(p["productId"] == 7777 and p["priceCents"] == 3100
                               for p in items))
    code, _ = request(LEGACY, "DELETE", "/legacy/products/7777")
    assert code == 204, code
    wait_for("product deletion propagates to search index",
             lambda: search("orchid"),
             lambda items: not any(p["productId"] == 7777 for p in items))
    print("PASS INSERT UPDATE DELETE product CDC")

    code, sale = request(LEGACY, "POST", "/legacy/sales",
                         {"customerId": 1, "items": [
                             {"productId": 101, "quantity": 2},
                             {"productId": 102, "quantity": 1}]})
    assert code == 201 and sale["lineCount"] == 2, (code, sale)
    sid = sale["saleId"]
    wait_for("sale + line-item aggregation 5,000 cents -> 100 cents bronze cashback",
             lambda: expense(sid),
             lambda d: d is not None and d["totalCents"] == 5000
             and d["cashbackCents"] == 100)
    wait_for("wallet credited once", lambda: wallet(1),
             lambda d: d is not None and d["balanceCents"] == 100)

    code, _ = request(LEGACY, "PUT", "/legacy/customers/1/tier", {"tier": "gold"})
    assert code == 200, code
    wait_for("customer tier CDC recalculates wallet policy to 10%",
             lambda: wallet(1),
             lambda d: d is not None and d["tier"] == "gold"
             and d["balanceCents"] == 500)
    wait_for("existing expense recalculated to gold tier",
             lambda: expense(sid),
             lambda d: d is not None and d["cashbackCents"] == 500)
    print("PASS CASHBACK without shared database or legacy code changes")
    print("ACCEPTANCE COMPLETE: DB WAL -> Debezium -> Kafka -> C# -> Elasticsearch + cashback DB")
    return sid

if __name__ == "__main__":
    main()
