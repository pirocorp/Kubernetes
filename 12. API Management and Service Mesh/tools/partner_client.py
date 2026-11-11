"""Call local or HTTPS Travelz partner API without putting secrets in command arguments."""
import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", required=True, help="http://127.0.0.1:5300 or trusted HTTPS Route")
    p.add_argument("--partner", choices=["red", "blue"], required=True)
    p.add_argument("--city", default="Paris")
    p.add_argument("--count", type=int, default=1)
    args = p.parse_args()
    if not 1 <= args.count <= 20:
        raise SystemExit("Count must be between 1 and 20")
    key = os.getenv("PARTNER_RED_KEY" if args.partner == "red" else "PARTNER_BLUE_KEY", "")
    if len(key) < 16:
        raise SystemExit("Source your local .runtime/keys.env, or set the key securely")
    url = args.base_url.rstrip("/") + "/partner/travels/" + urllib.parse.quote(args.city)
    for i in range(args.count):
        req = urllib.request.Request(url, headers={"X-Partner-Key": key})
        try:
            with urllib.request.urlopen(req, timeout=8) as r:
                status, data = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, data = e.code, e.read()
        try:
            payload = json.loads(data)
            print(f"{i + 1}: HTTP {status}; version={payload.get('version', '-')}; code={payload.get('code', '-')}")
        except ValueError:
            print(f"{i + 1}: HTTP {status}; non-JSON response")


if __name__ == "__main__":
    main()
