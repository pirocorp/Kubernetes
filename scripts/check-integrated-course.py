#!/usr/bin/env python3
"""Check topic-first Modules 01-08 against the modern labs and original theory."""
from __future__ import annotations
import posixpath
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "fcdbdecbc21edd51a64257bdc7760926b73a2598"
ROOT_LEGACY_SOURCE_COMMIT = "063ef92b3f09b3dc6f97a908db52390fec08ba65"
ROOT_LEGACY_MARKER = "<!-- ORIGINAL_ROOT_README_PRESERVED_START -->\n"
MODULES = {
    "01. Core Concepts": ("Readme.md", ["CORE-2026.md"]),
    "02. Cluster Setup and Management": ("README.md", ["SETUP-2026.md", "HOMEWORK-2026.md"]),
    "03. Security and Policies": ("README.md", ["SECURITY-2026.md"]),
    "04. Storage and Persistence": ("README.md", ["STORAGE-2026.md"]),
    "05. Advanced Concepts": ("README.md", ["ADVANCED-2026.md"]),
    "06. Observability and Troubleshooting": ("README.md", ["LAB-2026.md"]),
    "07. Templating Tools and Package Management": ("README.md", ["LAB-2026.md"]),
    "08. Exam Preparation": ("README.md", ["EXAM-2026.md"]),
}
MODERN = re.compile(r"<!-- MODERN_LAB_BEGIN ([A-Za-z0-9.-]+\.md) (\d+) -->\n(.*?)\n<!-- MODERN_LAB_END -->", re.DOTALL)
THEORY = re.compile(r"<!-- PRESERVED_THEORY_BEGIN -->\n(.*?)\n<!-- PRESERVED_THEORY_END -->", re.DOTALL)
FENCE = re.compile(r"^\s*(?:" + chr(96) * 3 + r"|~~~)")


def source(path: str, commit: str = SOURCE_COMMIT) -> str:
    result = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, check=True, capture_output=True)
    return result.stdout.decode("utf-8").replace("\r\n", "\n")


def current(path: str) -> str:
    return (ROOT / path).read_bytes().decode("utf-8").replace("\r\n", "\n")


def change_headings(text: str, delta: int) -> str:
    fenced = False
    result = []
    for line in text.split("\n"):
        if FENCE.match(line):
            fenced = not fenced
            result.append(line)
            continue
        match = None if fenced else re.match(r"^(#{1,6}) (.*)$", line)
        if match:
            length = len(match[1]) + delta
            result.append("#" * length + " " + match[2] if 1 <= length <= 6 else line)
        else:
            result.append(line)
    return "\n".join(result)


def split_guide(text: str) -> list[str]:
    text = text.replace("\r\n", "\n")
    lines = text.split("\n")
    cuts = [0]
    offset = 0
    fenced = False
    for line in lines:
        if not fenced and line.startswith("## ") and offset > 0:
            cuts.append(offset)
        if FENCE.match(line):
            fenced = not fenced
        offset += len(line) + 1
    cuts.append(len(text))
    return [text[a:b] for a, b in zip(cuts, cuts[1:])]


def normalize_approved_module_02_edits(segment: str) -> str:
    """Account only for intentional navigation repairs in Module 02.

    Keep an exact comparison for every other word in the 81 original lab
    fragments; the historical source is immutable.
    """
    replacements = (
        (
            "This is a companion to the original [Cluster Setup and Management notes](./README.md), which document the original Debian 10 / Kubernetes 1.21–1.22 exercises. Do **not** use those historical commands to install a new cluster.",
            "This **README is the complete supported lab**; historical Debian 10 / Kubernetes 1.21–1.22 procedures are no longer the execution path. Do **not** use historical commands to install a new cluster.",
        ),
        (
            "treat the [historical course notes](./README.md) as learning material and consult the current linked upstream instructions instead of copying their older commands.",
            "continue with the **current node maintenance, etcd, upgrade and HA exercises further down this README**, and consult the current upstream references listed in section 20.",
        ),
        (
            "following this guide plus the linked SETUP-2026.md is the supported 1.37 path.",
            "following this integrated README (sections 0–8 for setup) is the supported Kubernetes 1.37 path.",
        ),
    )
    for old, updated in replacements:
        segment = segment.replace(old, updated)
    return segment


def check_restored_sections(root: Path) -> list[str]:
    issues = []
    required = {
        "04. Storage and Persistence/README.md": (
            "## Git repository files in a Pod — `emptyDir` + init container (Kubernetes 1.37)",
            "./labs/git-pod-2026.yaml",
        ),
        "05. Advanced Concepts/README.md": (
            "## Horizontal Pod Autoscaler Example",
            "## Installing Ingress Controllers — Kubernetes 1.37 lab (2026)",
            "helm upgrade --install nginx-ingress",
            "kubectl apply -f https://github.com/kubernetes-sigs/metrics-server",
        ),
    }
    for file, tokens in required.items():
        source_text = (root / file).read_text(encoding="utf-8")
        for token in tokens:
            if token not in source_text:
                issues.append(f"{file}: missing restored exercise content {token!r}")
    if not (root / "04. Storage and Persistence/labs/git-pod-2026.yaml").is_file():
        issues.append("Module 04: missing actual init-container manifest")
    return issues


def markdown_links(content: str):
    fenced = False
    for line in content.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        for match in re.finditer(r"!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)", line):
            yield match[1].strip("<>")


def check_links(path: str, content: str) -> list[str]:
    failures = []
    for target in markdown_links(content):
        if target.startswith(("#", "//")) or re.match(r"^[A-Za-z][\w+.-]*:", target):
            continue
        raw = unquote(target.split("#", 1)[0].split("?", 1)[0])
        if not raw or "<" in raw or ">" in raw:
            continue
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), raw))
        if not (ROOT / resolved).exists():
            failures.append(f"{path} -> {target} (missing {resolved})")
    return failures


def run() -> int:
    failures = []
    link_count = 0
    modern_parts = 0
    theory_parts = 0
    for directory, (readme_name, guides) in MODULES.items():
        path = f"{directory}/{readme_name}"
        content = current(path)
        if "## Kubernetes 1.37 integrated labs" not in content:
            failures.append(f"{path}: missing integrated lab anchor")
        if "<!-- ORIGINAL_MODULE_README_PRESERVED_START -->" in content:
            failures.append(f"{path}: old duplicate lecture still appended")
        matches = list(MODERN.finditer(content))
        keys = [(m[1], int(m[2])) for m in matches]
        if len(keys) != len(set(keys)):
            failures.append(f"{path}: repeated modern lab sections")
        for guide in guides:
            guide_path = f"{directory}/{guide}"
            expected = split_guide(source(guide_path))
            for i, segment in enumerate(expected):
                found = [m[3] for m in matches if m[1] == guide and int(m[2]) == i]
                expected_section = change_headings(segment, +1)
                if directory == "02. Cluster Setup and Management":
                    expected_section = normalize_approved_module_02_edits(expected_section)
                if len(found) != 1 or found[0].strip() != expected_section.strip():
                    failures.append(f"{path}: modern {guide} section {i} missing or changed")
                else:
                    modern_parts += 1
            stub = current(guide_path)
            if f"./{readme_name}#" not in stub:
                failures.append(f"{guide_path}: compatibility pointer incorrect")
            link_count += len(list(markdown_links(stub)))
            failures.extend(check_links(guide_path, stub))
        if set(guide for guide, index in keys) != set(guides):
            failures.append(f"{path}: missing or unexpected lab guide markers")
        source_text = source(path)
        chunks = list(THEORY.finditer(content))
        if not chunks:
            failures.append(f"{path}: no original theory preserved")
        for match in chunks:
            original = change_headings(match[1].strip(), -1).strip()
            if not original or original not in source_text:
                failures.append(f"{path}: a theoretical fragment differs from the source lecture")
            else:
                theory_parts += 1
        link_count += len(list(markdown_links(content)))
        failures.extend(check_links(path, content))

    failures.extend(check_restored_sections(ROOT))
    root = current("README.md")
    original_root = source("README.md", ROOT_LEGACY_SOURCE_COMMIT)
    headings = list(re.finditer(r"(?m)^# Kubernetes$", original_root))
    if len(headings) != 1 or root.count(ROOT_LEGACY_MARKER) != 1:
        failures.append("root original lecture marker/source heading missing")
    elif root.split(ROOT_LEGACY_MARKER, 1)[1] != original_root[headings[0].start():]:
        failures.append("root original lecture not preserved exactly")
    if (ROOT / "COURSE-2026.md").exists() or (ROOT / "README-LEGACY-FOUNDATIONS.md").exists():
        failures.append("duplicate top-level course guide or lecture file")
    modules = re.findall(r"^\| (\d\d) — ", root, flags=re.MULTILINE)
    if modules != [f"{i:02d}" for i in range(16)]:
        failures.append(f"root README does not list 00–15 in order: {modules!r}")
    for path_obj in ROOT.rglob("*.md"):
        if ".git" in path_obj.parts:
            continue
        if "COURSE-2026.md" in path_obj.read_text(encoding="utf-8"):
            failures.append(f"{path_obj.relative_to(ROOT)}: stale removed course link")
    for path in ("README.md", "00. Resources/README.md"):
        content = current(path)
        link_count += len(list(markdown_links(content)))
        failures.extend(check_links(path, content))
    print(f"Modules audited: {len(MODULES)}")
    print(f"Modern lab sections verified against original guides: {modern_parts}")
    print(f"Original theory passages verified: {theory_parts}")
    print(f"Local Markdown links checked: {link_count}")
    print("Root course: 16 modules and verbatim original foundational lecture")
    if failures:
        for failure in failures:
            print("FAIL:", failure)
        print(f"FAIL: {len(failures)} issue(s)")
        return 1
    print("PASS: complete modern labs, grounded original theory, valid links")
    print("NOTE: static audit only; no live Kubernetes cluster testing")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
