#!/usr/bin/env python3
"""Validate the English and Korean pairs of repository documents.

Usage:
    python3 scripts/knowledge/check_bilingual.py [--root DIR] [--base REF]

Every `<name>.ko.md` needs a `<name>.md` beside it with the same number of
headings at each level. With --base, the change since REF must not add Korean
to a `.md` file and must update both files of a pair. Prints one
"path: problem" line per violation and exits 1 when any exist. CI runs this via
knowledge-check.yml.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

KO_SUFFIX = ".ko.md"
HANGUL = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]")
HEADING = re.compile(r"^(#{1,6}) ")
FENCE = re.compile(r"^\s*(```|~~~)")
DIFF_FILE = re.compile(r"^\+\+\+ b/(.+)$")
# The scenario tests still generate report.md in Korean.
KOREAN_ALLOWED_NAMES = frozenset({"report.md"})


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _english_path(ko_path: str) -> str:
    return ko_path.removesuffix(KO_SUFFIX) + ".md"


def _heading_counts(path: Path) -> Counter[int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0] == "---" and "---" in lines[1:]:
        lines = lines[lines.index("---", 1) + 1 :]
    counts: Counter[int] = Counter()
    fenced = False
    for line in lines:
        if FENCE.match(line):
            fenced = not fenced
        elif not fenced and (match := HEADING.match(line)):
            counts[len(match[1])] += 1
    return counts


def check_pairs(root: Path) -> list[str]:
    tracked = _git(root, "ls-files", "--cached", "--others", "--exclude-standard", f"*{KO_SUFFIX}")
    problems = []
    for ko_path in tracked.splitlines():
        en_path = _english_path(ko_path)
        if not (root / en_path).is_file():
            problems.append(f"{ko_path}: {en_path} is missing")
            continue
        ko_counts = _heading_counts(root / ko_path)
        en_counts = _heading_counts(root / en_path)
        if ko_counts != en_counts:
            problems.append(
                f"{ko_path}: headings differ from {en_path}: "
                f"{sorted(ko_counts.items())} and {sorted(en_counts.items())}"
            )
    return problems


def check_added_korean(root: Path, base: str) -> list[str]:
    diff = _git(root, "diff", "--unified=0", "--no-color", f"{base}...HEAD", "--", "*.md")
    problems = []
    current = ""
    for line in diff.splitlines():
        if match := DIFF_FILE.match(line):
            current = match[1]
        elif (
            line.startswith("+")
            and not line.startswith("+++")
            and not current.endswith(KO_SUFFIX)
            and Path(current).name not in KOREAN_ALLOWED_NAMES
            and HANGUL.search(line)
        ):
            problems.append(
                f"{current}: Korean added, move it to the .ko.md file: {line[1:].strip()}"
            )
    return problems


def check_pair_updates(root: Path, base: str) -> list[str]:
    changed = set(_git(root, "diff", "--name-only", f"{base}...HEAD", "--", "*.md").splitlines())
    problems = []
    for path in sorted(changed):
        if path.endswith(KO_SUFFIX):
            partner = _english_path(path)
        else:
            partner = path.removesuffix(".md") + KO_SUFFIX
            if not (root / partner).is_file():
                continue
        if partner not in changed:
            problems.append(f"{path}: changed without {partner}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base", help="check the change since this git ref")
    args = parser.parse_args()
    problems = check_pairs(args.root)
    if args.base:
        problems += check_added_korean(args.root, args.base)
        problems += check_pair_updates(args.root, args.base)
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
