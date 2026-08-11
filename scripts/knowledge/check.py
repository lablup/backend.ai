#!/usr/bin/env python3
"""Validate every KNOWLEDGE.md against the frontmatter schema.

Usage:
    python3 scripts/knowledge/check.py [--root DIR]

Schema violations (required fields, formats, status vocabulary, the
verified/generated invariant) are reported by `frontmatter.build_document`;
this script adds the environment checks — repo-wide name uniqueness,
scope/sources path existence, and resolvable body-relative markdown links
(fenced code blocks excluded). Prints one "path: problem" line per violation
and exits 1 when any exist. CI runs this via knowledge-check.yml.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from frontmatter import (
    KnowledgeDocument,
    ParseError,
    build_document,
    iter_knowledge_files,
    load,
)

LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "#")


def check_document(root: Path, path: Path, names: dict[str, str]) -> list[str]:
    relative_path = str(path.relative_to(root))
    try:
        raw, body_lines = load(path)
    except ParseError as exc:
        return [f"{relative_path}: {exc}"]

    document, schema_problems = build_document(raw)
    problems = [f"{relative_path}: {problem}" for problem in schema_problems]

    def problem(message: str) -> None:
        problems.append(f"{relative_path}: {message}")

    if document is not None:
        _check_environment(root, relative_path, document, names, problem)

    for target in _body_links(body_lines):
        resolved = (
            root / target.lstrip("/") if target.startswith("/") else path.parent / target
        )
        if not resolved.exists():
            problem(f"broken body link: {target}")

    return problems


def _check_environment(
    root: Path,
    relative_path: str,
    document: KnowledgeDocument,
    names: dict[str, str],
    problem,
) -> None:
    if document.name in names:
        problem(f"name {document.name!r} is already used by {names[document.name]}")
    else:
        names[document.name] = relative_path
    if not (root / document.scope).exists():
        problem(f"scope path does not exist: {document.scope}")
    for source in document.sources:
        if not (root / source).exists():
            problem(f"sources path does not exist: {source}")


def _body_links(body_lines: list[str]) -> list[str]:
    prose: list[str] = []
    in_fence = False
    for line in body_lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            prose.append(line)
    links: list[str] = []
    for target in LINK_PATTERN.findall("\n".join(prose)):
        if target.startswith(EXTERNAL_PREFIXES):
            continue
        path_part = target.split("#", 1)[0]
        if path_part:
            links.append(path_part)
    return links


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="repository root to check under (default: current directory)",
    )
    args = parser.parse_args()

    names: dict[str, str] = {}
    problems: list[str] = []
    checked = 0
    for path in iter_knowledge_files(args.root):
        problems.extend(check_document(args.root, path, names))
        checked += 1

    for line in problems:
        print(line)
    print(f"checked {checked} document(s), {len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
