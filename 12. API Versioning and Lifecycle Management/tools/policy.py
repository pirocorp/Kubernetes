"""Manage the local training gateway lifecycle state; no cluster-admin or external 3scale."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / ".runtime" / "lifecycle.json"
VALID = {"active", "deprecated", "sunset"}


def write(state):
    if state not in VALID:
        raise ValueError("state must be active, deprecated or sunset")
    POLICY.parent.mkdir(parents=True, exist_ok=True)
    temporary = POLICY.with_suffix(".tmp")
    temporary.write_text(json.dumps({"v1": state}, indent=2) + "\n", encoding="utf-8")
    temporary.replace(POLICY)
    print("Local gateway v1 state:", state)


def get():
    if not POLICY.exists():
        raise SystemExit("Missing policy. Run: python3 tools/policy.py set active")
    obj = json.loads(POLICY.read_text(encoding="utf-8"))
    if obj.get("v1") not in VALID:
        raise SystemExit("Invalid policy state")
    print(obj["v1"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["set", "get"])
    parser.add_argument("state", nargs="?")
    args = parser.parse_args()
    if args.action == "set":
        if args.state is None:
            parser.error("set requires active, deprecated or sunset")
        write(args.state)
    else:
        get()
