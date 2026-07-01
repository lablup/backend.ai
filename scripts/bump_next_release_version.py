#!/usr/bin/env python3
"""Advance NEXT_RELEASE_VERSION to the next sprint development version.

After a sprint release is cut, the NEXT_RELEASE_VERSION placeholder in meta.py
must move forward to the next development target. By default the sprint number is
incremented and the patch reset to zero ({year}.{sprint+1}.0). A new version may
be passed explicitly to handle year rollover or planned sprint skips.

The new version string is printed to stdout so the caller can reuse it (e.g. in a
commit message).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

META_PATH = Path("src/ai/backend/common/meta/meta.py")

VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
ASSIGNMENT_PATTERN = re.compile(r'^NEXT_RELEASE_VERSION = "[^"]+"$', re.MULTILINE)


def read_current_version() -> str:
    text = META_PATH.read_text()
    match = re.search(r'^NEXT_RELEASE_VERSION = "([^"]+)"$', text, re.MULTILINE)
    if match is None:
        print(f"Could not find NEXT_RELEASE_VERSION assignment in {META_PATH}", file=sys.stderr)
        sys.exit(1)
    return match.group(1)


def compute_next_version(current: str) -> str:
    match = VERSION_PATTERN.match(current)
    if match is None:
        print(
            f"Current NEXT_RELEASE_VERSION '{current}' is not in {{year}}.{{sprint}}.{{patch}} format",
            file=sys.stderr,
        )
        sys.exit(1)
    year, sprint, _patch = (int(part) for part in match.groups())
    return f"{year}.{sprint + 1}.0"


def write_version(new_version: str) -> None:
    text = META_PATH.read_text()
    new_text = ASSIGNMENT_PATTERN.sub(f'NEXT_RELEASE_VERSION = "{new_version}"', text, count=1)
    META_PATH.write_text(new_text)


def main() -> None:
    if len(sys.argv) > 2:
        print(f"Usage: {sys.argv[0]} [next_version]", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) == 2:
        next_version = sys.argv[1]
        if VERSION_PATTERN.match(next_version) is None:
            print(
                f"Provided next version '{next_version}' is not in {{year}}.{{sprint}}.{{patch}} format",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        next_version = compute_next_version(read_current_version())

    write_version(next_version)
    print(next_version)


if __name__ == "__main__":
    main()
