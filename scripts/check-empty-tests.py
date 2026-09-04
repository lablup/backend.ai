#!/usr/bin/env python3
"""Fail if any test module is empty.

An empty test file passes: pytest collects nothing from it and the target is reported as
succeeded, so a placeholder created and never filled counts toward "all tests pass" for as long as
nobody looks. Five of them shipped in one commit here and were green in every run afterwards,
including the runs used to argue the change was verified.

This lives in `scripts/` rather than as a test because pants runs each test target in a sandbox
holding only its own dependencies -- a test that walked the tree would see nothing but itself.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_ROOT = REPO_ROOT / "tests"

#: Empty before this check existed. Listed rather than ignored by pattern, so each one is a
#: visible debt that someone has to delete from here to clear.
KNOWN_EMPTY = frozenset({
    "tests/unit/common/test_provisionstage.py",
})


def empty_test_modules() -> list[Path]:
    return sorted(
        path
        for path in TESTS_ROOT.rglob("test_*.py")
        if path.is_file()
        and path.stat().st_size == 0
        and str(path.relative_to(REPO_ROOT)) not in KNOWN_EMPTY
    )


def main() -> int:
    empty = empty_test_modules()
    if not empty:
        return 0
    print("These test modules are empty, so they report success without asserting anything:")
    for path in empty:
        print(f"  {path.relative_to(REPO_ROOT)}")
    print("Fill them or delete them; a placeholder that passes is worse than a missing file.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
