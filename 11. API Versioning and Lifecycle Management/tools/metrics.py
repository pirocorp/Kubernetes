"""Read protected local gateway version metrics without leaking ADMIN_KEY in CLI args."""
import argparse
import json
import os
import urllib.error
import urllib.request

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8081")
    args = parser.parse_args()
    key = os.getenv("ADMIN_KEY", "")
    if len(key) < 16:
        raise SystemExit("Set ADMIN_KEY to at least 16 characters")
    req = urllib.request.Request(
        args.base_url.rstrip("/") + "/_metrics",
        headers={"X-Admin-Key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        raise SystemExit(f"Metrics HTTP error: {error.code}") from error
    print(json.dumps(payload, indent=2, sort_keys=True))
