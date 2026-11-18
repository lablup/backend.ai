#!/usr/bin/env python3
"""Check the names, types and front matter of the files in the news fragment directory.

The rules are in `changes/README.md`. Prints one line per broken file and exits 1.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from changelog_fragments import FragmentDirectory

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    errors = FragmentDirectory(REPO_ROOT).check()
    for error in errors:
        print(f"::error ::{error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
