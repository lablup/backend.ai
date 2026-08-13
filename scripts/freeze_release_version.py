#!/usr/bin/env python3
"""Freeze NEXT_RELEASE_VERSION references to the actual version string.

At release time, all usages of the NEXT_RELEASE_VERSION constant are replaced
with the actual version. Which form the replacement takes depends on where the
placeholder sits: a code reference becomes a quoted string literal, while a
comment -- the ``# Part of:`` line of an alembic migration -- becomes a bare
version string.

The constant definition in meta.py and its re-export in __init__.py remain
untouched for the next development cycle.

After running this script, run ``pants fix ::`` and ``pants fmt ::`` to remove
the now-unused NEXT_RELEASE_VERSION imports.
"""

from __future__ import annotations

import io
import re
import sys
import tokenize
from pathlib import Path

PLACEHOLDER = "NEXT_RELEASE_VERSION"

EXCLUDE_PATHS = {
    Path("src/ai/backend/common/meta/meta.py"),
    Path("src/ai/backend/common/meta/__init__.py"),
}

# Standalone import line:
#   from ai.backend.common.meta import NEXT_RELEASE_VERSION
#   from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
IMPORT_LINE_PATTERN = re.compile(
    rf"^from\s+ai\.backend\.common\.meta(?:\.meta)?\s+import\s+{PLACEHOLDER}\s*$"
)


def comment_columns(text: str) -> dict[int, int]:
    """Map each 1-based line number to the column where its comment starts."""
    columns: dict[int, int] = {}
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT:
            columns[token.start[0]] = token.start[1]
    return columns


def freeze_file(text: str, target_version: str) -> str:
    columns = comment_columns(text)
    new_lines: list[str] = []

    for lineno, line in enumerate(text.splitlines(keepends=True), start=1):
        stripped = line.strip()

        if IMPORT_LINE_PATTERN.match(stripped):
            continue

        # Remove NEXT_RELEASE_VERSION item from multi-line imports:
        #       NEXT_RELEASE_VERSION,
        if stripped == f"{PLACEHOLDER},":
            continue

        split_at = columns.get(lineno, len(line))
        code, comment = line[:split_at], line[split_at:]

        # Replace {NEXT_RELEASE_VERSION} in f-strings with literal text
        code = code.replace(f"{{{PLACEHOLDER}}}", target_version)
        comment = comment.replace(f"{{{PLACEHOLDER}}}", target_version)

        code = code.replace(PLACEHOLDER, f'"{target_version}"')
        comment = comment.replace(PLACEHOLDER, target_version)

        new_lines.append(code + comment)

    return "".join(new_lines)


def freeze_version(target_version: str) -> None:
    for path in Path("src").rglob("*.py"):
        if path in EXCLUDE_PATHS:
            continue

        text = path.read_text()
        if PLACEHOLDER not in text:
            continue

        path.write_text(freeze_file(text, target_version))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <target_version>", file=sys.stderr)
        sys.exit(1)
    freeze_version(sys.argv[1])
