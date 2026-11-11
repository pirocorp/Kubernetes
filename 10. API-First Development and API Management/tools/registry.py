"""Local immutable API artifact registry + conservative compatibility audit.

Uses the Python standard library. Educational substitute for the *concept*
of an API registry; it does not implement Apicurio Registry.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / ".registry"


def read_contract(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not data.get("openapi", "").startswith("3."):
        raise ValueError("Not an OpenAPI 3.x document")
    if not data.get("info", {}).get("version"):
        raise ValueError("Missing info.version")
    return data


def publish(path):
    data = read_contract(path)
    name = "products"
    version = data["info"]["version"]
    if "/" in version or ".." in version:
        raise ValueError("Invalid version")
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    target = REGISTRY / name / version
    manifest = target / "sha256.txt"
    if manifest.exists():
        if manifest.read_text().strip() != digest:
            raise ValueError("Immutable version conflict: increment info.version")
        print("Version already registered, same digest:", digest)
        return
    target.mkdir(parents=True, exist_ok=True)
    (target / "openapi.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    manifest.write_text(digest + "\n")
    print(f"Published {name}@{version}, SHA256: {digest}")


def check(old_path, new_path):
    old, new = read_contract(old_path), read_contract(new_path)
    issues = []
    for path, methods in old["paths"].items():
        if path not in new["paths"]:
            issues.append(f"Removed path {path}")
            continue
        for method, operation in methods.items():
            current = new["paths"][path].get(method)
            if current is None:
                issues.append(f"Removed {method.upper()} {path}")
                continue
            missing = set(operation.get("responses", {})) - set(current.get("responses", {}))
            if missing:
                issues.append(f"{method.upper()} {path}: removed response(s) {missing}")
    old_fields = set(old["components"]["schemas"]["Product"].get("required", []))
    new_fields = set(new["components"]["schemas"]["Product"].get("required", []))
    added_required = new_fields - old_fields
    if added_required:
        issues.append(f"New required Product response field(s): {added_required}")
    before_request = set(old["components"]["schemas"]["NewProduct"].get("required", []))
    after_request = set(new["components"]["schemas"]["NewProduct"].get("required", []))
    if after_request - before_request:
        issues.append("Added required request field(s)")
    for issue in issues:
        print("BREAKING:", issue)
    if issues:
        raise SystemExit(1)
    print("No breaking changes detected by the tutorial's limited rules.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pub = sub.add_parser("publish")
    pub.add_argument("contract")
    c = sub.add_parser("check")
    c.add_argument("old")
    c.add_argument("new")
    sub.add_parser("list")
    args = parser.parse_args()
    if args.command == "publish":
        publish(args.contract)
    elif args.command == "check":
        check(args.old, args.new)
    else:
        for file in sorted(REGISTRY.glob("products/*/sha256.txt")):
            print(file.parent.name, file.read_text().strip())


if __name__ == "__main__":
    main()
