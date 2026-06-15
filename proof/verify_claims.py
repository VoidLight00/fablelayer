#!/usr/bin/env python3
"""Verify public release claims for FableLayer.

This script is intentionally stdlib-only and suitable for CI.
It verifies claims that are stronger than ordinary unit tests:

- version alignment across public metadata
- plugin references exist
- internal build artifacts are not tracked
- root developer CLAUDE.md is not tracked
- tracked files do not contain local development path artifacts
- public governance files exist
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


LOCAL_ARTIFACT_PATTERNS = (
    "/Users/voidlight",
    "fablelayer-opus",
)

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".toml",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".sh",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def ok(message: str) -> None:
    print(f"ok: {message}")


def run(root: Path, args: list[str]) -> str:
    proc = subprocess.run(
        args,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        fail(f"command failed ({proc.returncode}): {' '.join(args)}\n{proc.stderr}")
    return proc.stdout


def git_tracked_files(root: Path) -> list[str]:
    out = run(root, ["git", "ls-files", "-z"])
    return [item for item in out.split("\0") if item]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="ignore")


def check_required_files(root: Path) -> None:
    required = [
        "README.md",
        "README.ko.md",
        "LICENSE",
        "NOTICE",
        "ATTRIBUTION.md",
        "CHANGELOG.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "ROADMAP.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        ".github/ISSUE_TEMPLATE/config.yml",
        "proof/CLAIMS.md",
        "proof/REPRODUCIBILITY.md",
        "proof/EXPERIMENT_DESIGN.md",
        "proof/THREATS_TO_VALIDITY.md",
    ]
    missing = [p for p in required if not (root / p).exists()]
    if missing:
        fail(f"missing required public files: {missing}")
    ok("required public files exist")


def check_version_alignment(root: Path) -> None:
    version = read_text(root / "VERSION").strip()
    if not version:
        fail("VERSION is empty")

    pyproject = read_text(root / "pyproject.toml")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', pyproject)
    if not match:
        fail("pyproject.toml version not found")
    py_version = match.group(1)

    plugin = json.loads(read_text(root / ".claude-plugin/plugin.json"))
    marketplace = json.loads(read_text(root / ".claude-plugin/marketplace.json"))
    market_meta_version = marketplace.get("metadata", {}).get("version")
    market_plugin_versions = [
        item.get("version") for item in marketplace.get("plugins", []) if isinstance(item, dict)
    ]

    values = [version, py_version, plugin.get("version"), market_meta_version, *market_plugin_versions]
    if any(v != version for v in values):
        fail(f"version mismatch: {values}")

    changelog = read_text(root / "CHANGELOG.md")
    if f"## {version} " not in changelog and f"## {version}—" not in changelog:
        fail(f"CHANGELOG.md does not contain a section for {version}")
    ok(f"version alignment is {version}")


def check_plugin_references(root: Path) -> None:
    plugin = json.loads(read_text(root / ".claude-plugin/plugin.json"))

    refs: list[str] = []
    refs.extend(plugin.get("skills", []))
    refs.extend(plugin.get("agents", []))

    claude_code = plugin.get("claude_code", {})
    if isinstance(claude_code, dict):
        refs.extend(
            item
            for item in [claude_code.get("skills_dir"), claude_code.get("agents_dir")]
            if isinstance(item, str)
        )

    layers = plugin.get("layers", {})
    if isinstance(layers, dict):
        refs.extend(item for item in layers.values() if isinstance(item, str))

    missing = [ref for ref in refs if not (root / ref).exists()]
    if missing:
        fail(f"plugin references missing paths: {missing}")
    ok("plugin references exist")


def check_not_tracked(root: Path, tracked: list[str]) -> None:
    workspace = [p for p in tracked if p == "_workspace" or p.startswith("_workspace/")]
    if workspace:
        fail(f"_workspace artifacts are tracked: {workspace[:10]}")
    if "CLAUDE.md" in tracked:
        fail("root CLAUDE.md is tracked")
    ok("internal workspace artifacts and root CLAUDE.md are not tracked")


def check_no_local_artifacts(root: Path, tracked: list[str]) -> None:
    # This checker defines the artifact patterns as string literals, so a naive
    # scan would match its own source. Exclude the checker file from the scan.
    try:
        self_rel = str(Path(__file__).resolve().relative_to(root))
    except ValueError:
        self_rel = None
    offenders: list[str] = []
    for rel in tracked:
        if self_rel is not None and rel == self_rel:
            continue
        path = root / rel
        if path.suffix not in TEXT_SUFFIXES:
            continue
        text = read_text(path)
        for pattern in LOCAL_ARTIFACT_PATTERNS:
            if pattern in text:
                offenders.append(f"{rel}: {pattern}")
    if offenders:
        fail("local development artifacts found in tracked files: " + "; ".join(offenders[:20]))
    ok("tracked text files contain no local development path artifacts")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not (root / ".git").exists():
        fail(f"not a git repository root: {root}")

    tracked = git_tracked_files(root)
    check_required_files(root)
    check_version_alignment(root)
    check_plugin_references(root)
    check_not_tracked(root, tracked)
    check_no_local_artifacts(root, tracked)
    ok("public claims verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

