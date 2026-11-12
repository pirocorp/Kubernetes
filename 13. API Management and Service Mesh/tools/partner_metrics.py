"""Retrieve protected partner metrics, without printing the admin secret."""
import argparse
import json
import os
import urllib.error
import urllib.request

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    args = p.parse_args()
    admin = os.getenv("ADMIN_KEY", "")
    if len(admin) < 16:
        raise SystemExit("Set ADMIN_KEY securely from .runtime/keys.env")
    req = urllib.request.Request(args.base_url.rstrip("/") + "/_metrics", headers={"X-Admin-Key": admin})
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            print(json.dumps(json.load(response), indent=2, sort_keys=True))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Metrics HTTP error: {e.code}") from e
