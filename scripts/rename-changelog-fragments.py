#!/usr/bin/env python3
"""Rename the news fragments named without a PR number to `<PR-number>.<type>.md` with `git mv`.

The PR number is the first `(#N)` in the subject of the first-parent commit that added the file.
Stops without renaming anything when a fragment name breaks the convention or has no PR number.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from changelog_fragments import NUMBERED_RE, UNNUMBERED_RE, is_fragment, load_fragment_settings

REPO_ROOT = Path(__file__).resolve().parent.parent
PR_NUMBER_RE = re.compile(r"\(#(\d+)\)")


class FragmentNameError(Exception):
    pass


def git(repo_root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo_root, check=True, capture_output=True, text=True
    ).stdout


def pr_number(repo_root: Path, path: Path) -> str:
    rel = path.relative_to(repo_root).as_posix()
    subjects = git(
        repo_root, "log", "--first-parent", "--diff-filter=A", "--format=%s", "--", rel
    ).splitlines()
    if not subjects:
        raise FragmentNameError(f"{rel}: no first-parent commit adds this file")
    # The newest addition is the one that produced the file now in the tree.
    match = PR_NUMBER_RE.search(subjects[0])
    if match is None:
        raise FragmentNameError(f"{rel}: no `(#N)` in the subject {subjects[0]!r}")
    return match.group(1)


def plan_renames(repo_root: Path) -> list[tuple[Path, Path]]:
    fragment_dir, types = load_fragment_settings(repo_root)
    taken = {p.name for p in fragment_dir.iterdir()}
    renames: list[tuple[Path, Path]] = []
    errors: list[str] = []
    for path in sorted(fragment_dir.iterdir()):
        name = path.name
        if not path.is_file() or not is_fragment(name, types) or NUMBERED_RE.match(name):
            continue
        match = UNNUMBERED_RE.match(name)
        if match is None or match.group("type") not in types:
            errors.append(
                f"{path.relative_to(repo_root)}: not `<PR-number>.<type>.md`"
                " nor `<YYYYMMDD>-<HHMMSS>-<6 chars>.<type>.md`"
            )
            continue
        try:
            number = pr_number(repo_root, path)
        except FragmentNameError as e:
            errors.append(str(e))
            continue
        fragment_type = match.group("type")
        target = f"{number}.{fragment_type}.md"
        counter = 0
        while target in taken:
            counter += 1
            target = f"{number}.{fragment_type}.{counter}.md"
        taken.add(target)
        renames.append((path, fragment_dir / target))
    if errors:
        raise FragmentNameError("\n".join(errors))
    return renames


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    repo_root = REPO_ROOT

    try:
        renames = plan_renames(repo_root)
    except FragmentNameError as e:
        for line in str(e).splitlines():
            print(f"::error ::{line}", file=sys.stderr)
        return 1
    for source, target in renames:
        git(repo_root, "mv", str(source.relative_to(repo_root)), str(target.relative_to(repo_root)))
        print(f"{source.name} -> {target.name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
