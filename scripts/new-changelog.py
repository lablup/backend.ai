#!/usr/bin/env python3
"""Write a news fragment named without a PR number and print its path.

Usage: `python3 scripts/new-changelog.py <type> "<sentence>"`.
The release renames it to `<PR-number>.<type>.md` (`rename-changelog-fragments.py`).
"""

from __future__ import annotations

import argparse
import secrets
import string
import sys
from datetime import UTC, datetime
from pathlib import Path

from changelog_fragments import load_fragment_settings

REPO_ROOT = Path(__file__).resolve().parent.parent
SUFFIX_ALPHABET = string.ascii_lowercase + string.digits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("type", help="Fragment type, a `directory` of `[[tool.towncrier.type]]`")
    parser.add_argument("sentence", help="Single-line English sentence")
    args = parser.parse_args()

    fragment_dir, types = load_fragment_settings(REPO_ROOT)
    if args.type not in types:
        print(f"Unknown type {args.type!r}; expected one of: {', '.join(types)}", file=sys.stderr)
        return 1
    sentence = args.sentence.strip()
    if not sentence or "\n" in sentence:
        print("The sentence must be a single non-empty line", file=sys.stderr)
        return 1

    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    suffix = "".join(secrets.choice(SUFFIX_ALPHABET) for _ in range(6))
    name = f"{stamp}-{suffix}.{args.type}.md"
    path = fragment_dir / name
    with path.open("x") as f:
        f.write(sentence + "\n")
    print(path.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
