"""Sample observed responses via a portal endpoint (not proof of mesh without sidecars)."""
import argparse
import json
import urllib.error
import urllib.request
from collections import Counter

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    p.add_argument("--count", type=int, default=30)
    args = p.parse_args()
    if not 1 <= args.count <= 100:
        raise SystemExit("count must be 1..100")
    versions = Counter()
    for i in range(args.count):
        req = urllib.request.Request(args.base_url.rstrip("/") + "/portal/Paris")
        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                body = json.load(response)
                version = body["quote"]["version"]
                if version not in ("v1", "v2"):
                    raise ValueError("Unexpected service version")
                versions[version] += 1
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError, ValueError) as error:
            raise SystemExit(f"Request {i+1} failed: {error}") from error
    print("Observed versions (sample, not exact guaranteed ratio):")
    for version in ("v1", "v2"):
        print(version, versions[version])
