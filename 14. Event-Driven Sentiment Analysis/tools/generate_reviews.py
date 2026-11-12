"""Send synthetic reviews to Globex, for Grafana/Influx and Kafka demonstrations."""
import argparse
import json
import os
import random
import urllib.error
import urllib.request

CONTENT = [
    "I love this amazing product", "It is good and excellent",
    "This one is broken and awful", "Bad and slow delivery",
    "Great value", "Arrived as described", "This is spam"
]
CATEGORIES = ["clothing", "bags", "electronics", "sports-equipment"]


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", default="http://127.0.0.1:5080")
    p.add_argument("--count", type=int, default=30)
    args = p.parse_args()
    if not 1 <= args.count <= 200:
        raise SystemExit("count must be 1..200")
    rng = random.Random(13)
    for index in range(args.count):
        payload = {
            "productId": f"demo-{index:03d}",
            "category": rng.choice(CATEGORIES),
            "text": rng.choice(CONTENT)
        }
        req = urllib.request.Request(args.base_url.rstrip("/") + "/reviews",
            data=json.dumps(payload).encode(), method="POST",
            headers={"Content-Type": "application/json",
                     **({"X-Api-Key": os.environ["INGEST_KEY"]} if os.getenv("INGEST_KEY") else {})})
        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status != 202: raise RuntimeError(response.status)
        except urllib.error.HTTPError as ex:
            raise SystemExit(f"Review {index} HTTP {ex.code}") from ex
    print(f"Submitted {args.count} synthetic review events; processing is asynchronous.")
