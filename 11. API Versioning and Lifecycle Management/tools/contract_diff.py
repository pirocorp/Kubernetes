"""Small educational OpenAPI compatibility checker; not a full semantic diff tool."""
import argparse
import json
from pathlib import Path


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("openapi") != "3.0.3" or "OrderRequest" not in data.get("components", {}).get("schemas", {}):
        raise SystemExit("Expected the supplied OpenAPI 3.0.3 OrderRequest contract")
    return data


def compare(old, new):
    issues = []
    old_paths = set(old["paths"])
    new_paths = set(new["paths"])
    for lost in old_paths - new_paths:
        issues.append(f"Removed path: {lost}")
    old_schema = old["components"]["schemas"]["OrderRequest"]
    new_schema = new["components"]["schemas"]["OrderRequest"]
    lost_fields = set(old_schema["properties"]) - set(new_schema["properties"])
    new_required = set(new_schema["required"]) - set(old_schema["required"])
    if lost_fields:
        issues.append(f"Removed request field(s): {', '.join(sorted(lost_fields))}")
    if new_required:
        issues.append(f"Added mandatory request field(s): {', '.join(sorted(new_required))}")
    for key in set(old_schema["properties"]) & set(new_schema["properties"]):
        if old_schema["properties"][key].get("type") != new_schema["properties"][key].get("type"):
            issues.append(f"Changed field type: {key}")
    return issues


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("previous")
    parser.add_argument("candidate")
    args = parser.parse_args()
    old, new = load(args.previous), load(args.candidate)
    issues = compare(old, new)
    print(f"Comparing {old['info']['version']} -> {new['info']['version']}")
    if issues:
        for item in issues:
            print("BREAKING (if replacing the previous contract):", item)
        print("Recommendation: publish a new major API alongside the existing endpoint.")
        raise SystemExit(2)
    added = set(new["components"]["schemas"]["OrderRequest"]["properties"]) - set(
        old["components"]["schemas"]["OrderRequest"]["properties"]
    )
    print("COMPATIBLE under this check. New optional fields:", ", ".join(sorted(added)) or "(none)")
    print("Note: this is a limited teaching checker; it cannot prove semantic compatibility.")
