#!/usr/bin/env python3
"""Static fidelity and navigation audit for the integrated Kubernetes 1.37 modules.

Compares integrated README files against the source Markdown at the last
pre-integration main commit. The historical lecture must be preserved exactly
and the complete modern lab text must be present (headings may be demoted by
one level for integration). This is not a substitute for real cluster tests.
"""
from __future__ import annotations

import posixpath
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "fcdbdecbc21edd51a64257bdc7760926b73a2598"
ROOT_LEGACY_SOURCE_COMMIT = "063ef92b3f09b3dc6f97a908db52390fec08ba65"
ROOT_LEGACY_MARKER = "<!-- HISTORICAL_ROOT_README_PRESERVED_START -->\n"
MARKER = "<!-- ORIGINAL_MODULE_README_PRESERVED_START -->\n"
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


def source(path: str, commit: str = SOURCE_COMMIT) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT, check=True, capture_output=True,
    )
    return result.stdout.decode("utf-8")


def current(path: str) -> str:
    return (ROOT / path).read_bytes().decode("utf-8")


def bump_headings(text: str) -> str:
    """Exactly the one-level Markdown demotion used by the integration."""
    fenced = False
    result = []
    for line in text.split("\n"):
        if re.match(r"^\s*(\x60{3}|~~~)", line):
            fenced = not fenced
            result.append(line)
            continue
        match = None if fenced else re.match(r"^(#{1,5}) (.*)$", line)
        result.append("#" * (len(match[1]) + 1) + " " + match[2] if match else line)
    return "\n".join(result)


def markdown_links(content: str):
    fenced = False
    for line in content.splitlines():
        if re.match(r"^\s*(\x60{3}|~~~)", line):
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
    for directory, (readme_name, guides) in MODULES.items():
        path = f"{directory}/{readme_name}"
        text = current(path)
        if text.count(MARKER) != 1:
            failures.append(f"{path}: missing or repeated original-lecture marker")
            continue
        modern, historical = text.split(MARKER, 1)
        if historical != source(path):
            failures.append(f"{path}: original 2021 lecture was modified or truncated")
        for guide in guides:
            guide_path = f"{directory}/{guide}"
            expected = bump_headings(source(guide_path)).rstrip()
            if expected not in modern:
                failures.append(f"{path}: not all original 2026 content from {guide} is integrated")
            stub = current(guide_path)
            if f"./{readme_name}#" not in stub:
                failures.append(f"{guide_path}: compatibility pointer absent")
            links = list(markdown_links(stub))
            link_count += len(links)
            failures.extend(check_links(guide_path, stub))
        if "## Kubernetes 1.37 integrated labs" not in modern:
            failures.append(f"{path}: canonical integrated lab heading missing")
        links = list(markdown_links(modern))
        link_count += len(links)
        failures.extend(check_links(path, modern))
    # The root README is now the only course guide.
    root = current("README.md")
    archived = current("README-LEGACY-FOUNDATIONS.md")
    original_root = source("README.md", ROOT_LEGACY_SOURCE_COMMIT)
    root_headings = list(re.finditer(r"(?m)^# Kubernetes$", original_root))
    if len(root_headings) != 1:
        failures.append("historical root source lacks a unique level-one Kubernetes heading")
    elif archived.count(ROOT_LEGACY_MARKER) != 1 or archived.split(ROOT_LEGACY_MARKER, 1)[1] != original_root[root_headings[0].start():]:
        failures.append("original root README lecture was not preserved verbatim")
    if (ROOT / "COURSE-2026.md").exists():
        failures.append("COURSE-2026.md still exists: the root README should be the single course guide")
    modules = re.findall(r"^\| (\d\d) — ", root, flags=re.MULTILINE)
    if modules != [f"{i:02d}" for i in range(16)]:
        failures.append(f"course README must link Modules 00–15 in order; found {modules!r}")
    for path_obj in ROOT.rglob("*.md"):
        if ".git" in path_obj.parts:
            continue
        if "COURSE-2026.md" in path_obj.read_text(encoding="utf-8"):
            failures.append(f"{path_obj.relative_to(ROOT)}: stale reference to deleted COURSE-2026.md")
    for path in ("README.md", "README-LEGACY-FOUNDATIONS.md", "00. Resources/README.md"):
        text = current(path)
        links = list(markdown_links(text))
        link_count += len(links)
        # Both the current course hub and archived original are validated.
        failures.extend(check_links(path, text))
    print(f"Integrated chapters audited: {len(MODULES)}")
    print("Original 2021 lecture and full 2026 guides compared against", SOURCE_COMMIT[:12])
    print("Course hub: 16 module links and no stale COURSE-2026.md references")
    print("Legacy root lecture: checked against", ROOT_LEGACY_SOURCE_COMMIT[:12])
    print(f"Local Markdown links checked in supported material: {link_count}")
    if failures:
        for failure in failures:
            print("FAIL:", failure)
        print(f"FAIL: {len(failures)} audit issue(s)")
        return 1
    print("PASS: original lessons preserved, full modern labs integrated, links resolve")
    print("NOTE: no Kubernetes cluster/runtime tests were performed here")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
