#!/usr/bin/env python3
"""Write a news fragment named without a PR number and print its path.

Usage: `python3 scripts/new-changelog.py <type> "<sentence>" [--issue <key>] [--epic <key>]`.
The release renames it to `<PR-number>.<type>.md` (`rename-changelog-fragments.py`).
"""

from __future__ import annotations

import argparse
import secrets
import string
import sys
from datetime import UTC, datetime
from pathlib import Path

from changelog_fragments import FRONT_MATTER_DELIMITER, FragmentDirectory, FragmentError

REPO_ROOT = Path(__file__).resolve().parent.parent
SUFFIX_ALPHABET = string.ascii_lowercase + string.digits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("type", help="Fragment type, a `directory` of `[[tool.towncrier.type]]`")
    parser.add_argument("sentence", help="Single-line English sentence")
    parser.add_argument("--issue", help="Issue key (`BA-N` or `BAI-N`)")
    parser.add_argument("--epic", help="Epic key of the issue (`BA-N` or `BAI-N`)")
    args = parser.parse_args()

    fragments = FragmentDirectory(REPO_ROOT)
    sentence = args.sentence.strip()
    if not sentence or "\n" in sentence:
        print("The sentence must be a single non-empty line", file=sys.stderr)
        return 1

    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    suffix = "".join(secrets.choice(SUFFIX_ALPHABET) for _ in range(6))
    path = fragments.path / f"{stamp}-{suffix}.{args.type}.md"
    fields = [
        f"{key}: {value}" for key, value in (("issue", args.issue), ("epic", args.epic)) if value
    ]
    lines = [FRONT_MATTER_DELIMITER, *fields, FRONT_MATTER_DELIMITER] if fields else []
    with path.open("x") as f:
        f.write("\n".join([*lines, sentence]) + "\n")
    try:
        fragments.check_file(path)
    except FragmentError as e:
        path.unlink()
        print(e, file=sys.stderr)
        return 1
    print(fragments.rel(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
