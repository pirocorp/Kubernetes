#!/usr/bin/env python3
"""Static integrity tests; no live Kubernetes/OpenShift execution claimed."""
from __future__ import annotations
import json
import pathlib
import subprocess
import sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
M09 = ROOT / "09. OpenShift/labs/examples/quotes-stack/frontend"
M10 = ROOT / "10. Full-Stack JavaScript on OpenShift"


def require(ok, reason):
    if not ok:
        raise AssertionError(reason)


def mod09():
    package = json.loads((M09 / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((M09 / "package-lock.json").read_text(encoding="utf-8"))
    require(lock["lockfileVersion"] == 3, "npm lock v3 required")
    require(lock["packages"][""]["dependencies"] == package["dependencies"],
            "package-lock and package.json disagree")
    require(len(lock["packages"]) >= 30, "transitive dependencies are not pinned")
    lab = (ROOT / "09. OpenShift/labs/LAB-04-FULLSTACK-2026.md").read_text(encoding="utf-8")
    require("npm ci --ignore-scripts" in lab, "Module 09 missing reproducible npm ci")
    print("PASS Module 09 pinned dependency tree")


def mod10():
    for variant in ("pvc", "ephemeral"):
        docs = list(yaml.safe_load_all((M10 / "openshift" / f"postgres-{variant}.yaml").read_text()))
        objects = {d["kind"]: d for d in docs}
        require("Service" in objects and "Deployment" in objects, variant + " objects missing")
        svc, dep = objects["Service"], objects["Deployment"]
        require(svc["metadata"]["name"] == "m10-postgres", variant + " service name")
        require(svc["spec"]["type"] == "ClusterIP", variant + " public database")
        require(svc["spec"]["ports"][0]["port"] == 5432, variant + " wrong port")
        require(dep["spec"]["strategy"]["type"] == "Recreate", variant + " concurrent writers")
        pod = dep["spec"]["template"]
        require(all(pod["metadata"]["labels"].get(k) == v
                    for k, v in svc["spec"]["selector"].items()),
                variant + " Service selector does not match Pod")
        c = pod["spec"]["containers"][0]
        require("postgresql-16-c9s:" in c["image"], variant + " wrong Postgres image")
        require({e["name"] for e in c["env"]} ==
                {"POSTGRESQL_USER", "POSTGRESQL_DATABASE", "POSTGRESQL_PASSWORD"},
                variant + " invalid variables")
        require(all(e.get("valueFrom", {}).get("secretKeyRef", {}).get("name") == "m10-postgres-auth"
                    for e in c["env"]), variant + " credentials not secret-backed")
        require(c["volumeMounts"][0]["mountPath"] == "/var/lib/pgsql/data", variant + " wrong volume")
        volume = pod["spec"]["volumes"][0]
        if variant == "pvc":
            require("PersistentVolumeClaim" in objects and
                    volume["persistentVolumeClaim"]["claimName"] == "m10-postgres-data",
                    "wrong persistent volume path")
        else:
            require("PersistentVolumeClaim" not in objects and "emptyDir" in volume,
                    "ephemeral fallback still requires a StorageClass")
    lab = (M10 / "labs/LAB-03-POSTGRESQL.md").read_text(encoding="utf-8")
    for name in ("postgres-pvc.yaml", "postgres-ephemeral.yaml", "m10-db-url", "short_links"):
        require(name in lab, "Module 10-C missing " + name)
    print("PASS Module 10 PVC/emptyDir and common Service/Secret contract")


def credentials():
    env, runtime = M10 / ".env", M10 / ".runtime"
    require(not env.exists() and not runtime.exists(), "credential test requires clean CI checkout")
    try:
        for name in ("init_env.py", "prepare_oc.py"):
            subprocess.run([sys.executable, "tools/" + name], cwd=M10, check=True,
                           capture_output=True)
        paths = (env, runtime / "postgres.params", runtime / "database.env",
                 runtime / "postgres-auth.env")
        for path in paths:
            require(path.exists() and path.stat().st_mode & 0o777 == 0o600,
                    "missing or insecure credential file: " + str(path))
        password = env.read_text().strip().split("=", 1)[1]
        require("POSTGRESQL_PASSWORD=" + password in
                (runtime / "postgres-auth.env").read_text(), "inconsistent auth password")
        require(password in (runtime / "database.env").read_text(), "DB URL password mismatch")
        print("PASS Module 10 generated credentials (0600, consistent secrets)")
    finally:
        for path in (runtime / "postgres-auth.env", runtime / "database.env",
                     runtime / "postgres.params", env):
            if path.exists():
                path.unlink()
        if runtime.exists():
            runtime.rmdir()


def profiles():
    subprocess.run(["bash", "-n", str(ROOT / "scripts/check-openshift-profile.sh")],
                   check=True)
    doc = (ROOT / "docs/OPENSHIFT-LAB-PROFILES.md").read_text()
    for section in ("Module 09-E", "Module 10-C", "Module 13-E",
                    "Module 14-E", "Module 15-E"):
        require(section in doc, "missing profile " + section)
    for path in ("README.md", "09. OpenShift/README.md",
                 "10. Full-Stack JavaScript on OpenShift/README.md",
                 "13. API Management and Service Mesh/README.md",
                 "14. Event-Driven Sentiment Analysis/README.md",
                 "15. CDC Legacy Modernization/README.md"):
        require("OPENSHIFT-LAB-PROFILES.md" in (ROOT / path).read_text(),
                "missing platform profile link in " + path)
    for path, required in (
        ("04. Storage and Persistence/README.md",
         ["## Git repository files in a Pod"]),
        ("05. Advanced Concepts/README.md",
         ["## Horizontal Pod Autoscaler Example",
          "## Installing Ingress Controllers — Kubernetes 1.37 lab (2026)"]),
    ):
        content = (ROOT / path).read_text()
        for item in required:
            require(item in content, path + " missing " + item)
    print("PASS supported modules and external platform preflight boundaries")


def main():
    mod09()
    mod10()
    credentials()
    profiles()
    print("PASS static self-sufficiency checks; live cluster not tested")


if __name__ == "__main__":
    main()
