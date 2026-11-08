#!/usr/bin/env python3
"""Turn the news fragments named without a PR number into `<PR-number>.<type>.md` for towncrier.

Each one is renamed with `git mv` and its front matter is dropped. The PR number is the first
`(#N)` in the subject of the first-parent commit that added the file.
Stops without changing anything when a file in the fragment directory breaks the rules
(`validate-changelog-fragments.py`) or a fragment has no PR number.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from changelog_fragments import FragmentDirectory, FragmentError, UnnumberedFragment

REPO_ROOT = Path(__file__).resolve().parent.parent
PR_NUMBER_RE = re.compile(r"\(#(\d+)\)")


class FragmentRenamer:
    fragments: FragmentDirectory

    def __init__(self, fragments: FragmentDirectory) -> None:
        self.fragments = fragments

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=self.fragments.repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def pr_number(self, fragment: UnnumberedFragment) -> str:
        rel = self.fragments.rel(fragment.path)
        subjects = self.git(
            "log", "--first-parent", "--diff-filter=A", "--format=%s", "--", rel
        ).splitlines()
        if not subjects:
            raise FragmentError(f"{rel}: no first-parent commit adds this file")
        # The newest addition is the one that produced the file now in the tree.
        match = PR_NUMBER_RE.search(subjects[0])
        if match is None:
            raise FragmentError(f"{rel}: no `(#N)` in the subject {subjects[0]!r}")
        return match.group(1)

    def plan(self) -> list[tuple[UnnumberedFragment, Path]]:
        taken = {p.name for p in self.fragments.path.iterdir()}
        renames: list[tuple[UnnumberedFragment, Path]] = []
        errors: list[str] = []
        for fragment in self.fragments.unnumbered_fragments():
            try:
                number = self.pr_number(fragment)
            except FragmentError as e:
                errors.append(str(e))
                continue
            target = f"{number}.{fragment.type}.md"
            counter = 0
            while target in taken:
                counter += 1
                target = f"{number}.{fragment.type}.{counter}.md"
            taken.add(target)
            renames.append((fragment, self.fragments.path / target))
        if errors:
            raise FragmentError("\n".join(errors))
        return renames

    def apply(self, renames: list[tuple[UnnumberedFragment, Path]]) -> None:
        for fragment, target in renames:
            self.git("mv", self.fragments.rel(fragment.path), self.fragments.rel(target))
            target.write_text(fragment.body + "\n")
            self.git("add", self.fragments.rel(target))
            print(f"{fragment.path.name} -> {target.name}", file=sys.stderr)


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    renamer = FragmentRenamer(FragmentDirectory(REPO_ROOT))
    try:
        renames = renamer.plan()
    except FragmentError as e:
        for line in str(e).splitlines():
            print(f"::error ::{line}", file=sys.stderr)
        return 1
    renamer.apply(renames)
    return 0


if __name__ == "__main__":
    sys.exit(main())
