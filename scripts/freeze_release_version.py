#!/usr/bin/env python3
"""Freeze NEXT_RELEASE_VERSION references to the actual version string.

At release time, all usages of the NEXT_RELEASE_VERSION constant are replaced
with the actual version string literal. The constant definition in meta.py and
its re-export in __init__.py remain untouched for the next development cycle.

After running this script, run ``pants fix ::`` and ``pants fmt ::`` to remove
the now-unused NEXT_RELEASE_VERSION imports.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

EXCLUDE_PATHS = {
    Path("src/ai/backend/common/meta/meta.py"),
    Path("src/ai/backend/common/meta/__init__.py"),
}


def freeze_version(target_version: str) -> None:
    for path in Path("src").rglob("*.py"):
        if path in EXCLUDE_PATHS:
            continue

        text = path.read_text()
        if "NEXT_RELEASE_VERSION" not in text:
            continue

        lines = text.splitlines(keepends=True)
        new_lines: list[str] = []

        for line in lines:
            stripped = line.strip()

            # Remove standalone import line:
            #   from ai.backend.common.meta import NEXT_RELEASE_VERSION
            #   from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
            if re.match(
                r"^from\s+ai\.backend\.common\.meta(?:\.meta)?\s+import\s+NEXT_RELEASE_VERSION\s*$",
                stripped,
            ):
                continue

            # Remove NEXT_RELEASE_VERSION item from multi-line imports:
            #       NEXT_RELEASE_VERSION,
            if stripped == "NEXT_RELEASE_VERSION,":
                continue

            # Replace {NEXT_RELEASE_VERSION} in f-strings with literal text
            line = line.replace("{NEXT_RELEASE_VERSION}", target_version)

            # Replace remaining NEXT_RELEASE_VERSION with quoted string literal
            line = line.replace("NEXT_RELEASE_VERSION", f'"{target_version}"')

            new_lines.append(line)

        path.write_text("".join(new_lines))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <target_version>", file=sys.stderr)
        sys.exit(1)
    freeze_version(sys.argv[1])
