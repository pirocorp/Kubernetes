"""Local Travelz exercise verification, Python 3.10+ standard library."""
import argparse
import json
import os
import urllib.error
import urllib.request

PORTS = (5100, 5101, 5102, 5200, 5300)


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def json_get(url, headers=None):
    status, body = get(url, headers)
    return status, json.loads(body)


def basic():
    for port in PORTS:
        status, body = get(f"http://127.0.0.1:{port}/healthz")
        assert status == 200 and body.strip() == "ok", (port, status, body)
        print("PASS health", port)
    for port, major in [(5101, "v1"), (5102, "v2")]:
        status, quote = json_get(f"http://127.0.0.1:{port}/api/travels/Paris")
        assert status == 200 and quote["version"] == major, (port, status, quote)
        print("PASS agency", major)
    status, portal = json_get("http://127.0.0.1:5100/portal/Paris")
    assert status == 200 and portal["channel"] == "travel-portal" and portal["quote"]["version"] in ("v1", "v2")
    assert portal["correlationId"] == portal["quote"]["correlationId"], portal
    print("PASS portal-to-agency correlation")
    status, _ = json_get("http://127.0.0.1:5300/partner/travels/Paris")
    assert status == 401, status
    print("PASS partner access denied without credentials")


def canary():
    before_status, before = json_get("http://127.0.0.1:5200/_stats")
    assert before_status == 200
    for _ in range(20):
        status, _ = json_get("http://127.0.0.1:5200/api/travels/Paris")
        assert status == 200, status
    _, after = json_get("http://127.0.0.1:5200/_stats")
    v1 = after.get("selected_v1", 0) - before.get("selected_v1", 0)
    v2 = after.get("selected_v2", 0) - before.get("selected_v2", 0)
    assert (v1, v2) == (16, 4), (v1, v2)
    print(f"PASS deterministic local 80/20 demonstration: v1={v1}, v2={v2}")


def fallback():
    _, before = json_get("http://127.0.0.1:5200/_stats")
    for _ in range(5):
        status, quote = json_get("http://127.0.0.1:5200/api/travels/Failover")
        assert status == 200 and quote["version"] == "v1", (status, quote)
    _, after = json_get("http://127.0.0.1:5200/_stats")
    retries = after.get("retry_to_v1", 0) - before.get("retry_to_v1", 0)
    assert retries == 1, retries
    print("PASS one simulated v2 failure recovered by v1 GET retry")


def partner():
    red = os.getenv("PARTNER_RED_KEY", "")
    blue = os.getenv("PARTNER_BLUE_KEY", "")
    admin = os.getenv("ADMIN_KEY", "")
    if min(map(len, (red, blue, admin))) < 16:
        raise SystemExit("Source .runtime/keys.env first")
    # Run right after service restart so the quota window is empty.
    for i in range(4):
        status, quote = json_get("http://127.0.0.1:5300/partner/travels/Paris",
                                 {"X-Partner-Key": red})
        expected = 200 if i < 3 else 429
        assert status == expected, (i, status, quote)
        if status == 200:
            assert quote["version"] == "v2"
    status, quote = json_get("http://127.0.0.1:5300/partner/travels/Paris",
                             {"X-Partner-Key": blue})
    assert status == 200 and quote["version"] == "v2", (status, quote)
    status, metrics = json_get("http://127.0.0.1:5300/_metrics",
                              {"X-Admin-Key": admin})
    assert status == 200 and metrics["counts"]["limited_red"] >= 1, metrics
    print("PASS red 3+429, blue 200, protected partner analytics")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("test", choices=["basic", "canary", "fallback", "partner"])
    args = parser.parse_args()
    globals()[args.test]()
