#!/usr/bin/env python3
"""Freeze NEXT_RELEASE_VERSION references to the actual version string.

At release time, all usages of the NEXT_RELEASE_VERSION constant are replaced
with the actual version. Which form the replacement takes depends on where the
placeholder sits: a code reference becomes a quoted string literal, while a
comment -- the ``# Part of:`` line of an alembic migration -- becomes a bare
version string.

The constant definition in meta.py and its re-export in __init__.py remain
untouched for the next development cycle.

NEXT_RELEASE_VERSION is removed from its imports; an import left with no name is removed.
The comments inside a rewritten import move to the end of its line.
An import of NEXT_RELEASE_VERSION the script cannot rewrite safely stops it before any file is written:
an alias, a module other than ai.backend.common.meta(.meta), the only statement of a block,
or another statement on the same line.
After running this script, run ``ruff format`` on the changed files (``scripts/release.sh`` does).
"""

from __future__ import annotations

import ast
import io
import sys
import tokenize
from pathlib import Path

PLACEHOLDER = "NEXT_RELEASE_VERSION"

EXCLUDE_PATHS = {
    Path("src/ai/backend/common/meta/meta.py"),
    Path("src/ai/backend/common/meta/__init__.py"),
}

META_MODULES = {"ai.backend.common.meta", "ai.backend.common.meta.meta"}


class UnsupportedImportError(Exception):
    pass


def comment_columns(text: str) -> dict[int, int]:
    """Map each 1-based line number to the column where its comment starts."""
    columns: dict[int, int] = {}
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT:
            columns[token.start[0]] = token.start[1]
    return columns


def check_import(node: ast.ImportFrom, parent: ast.AST, siblings: list[ast.stmt]) -> None:
    def reject(reason: str) -> UnsupportedImportError:
        return UnsupportedImportError(f"line {node.lineno}: {PLACEHOLDER} {reason}")

    if node.level or node.module not in META_MODULES:
        raise reject("is imported from a module other than ai.backend.common.meta(.meta)")
    if any(alias.name == PLACEHOLDER and alias.asname for alias in node.names):
        raise reject("is imported under an alias")
    in_block = not isinstance(parent, ast.Module)
    if in_block and len(siblings) == 1:
        raise reject("is imported by the only statement of a block")
    index = siblings.index(node)
    before = siblings[index - 1] if index > 0 else None
    after = siblings[index + 1] if index + 1 < len(siblings) else None
    if (
        (in_block and getattr(parent, "lineno", None) == node.lineno)
        or (before is not None and before.end_lineno == node.lineno)
        or (after is not None and after.lineno == node.end_lineno)
    ):
        raise reject("is imported on a line shared with another statement")


def placeholder_imports(text: str) -> dict[int, tuple[int, str]]:
    """Map the first line of each import of NEXT_RELEASE_VERSION to its last line and its rewrite."""
    imports: dict[int, tuple[int, str]] = {}
    for parent in ast.walk(ast.parse(text)):
        for _, siblings in ast.iter_fields(parent):
            if not isinstance(siblings, list):
                continue
            for node in siblings:
                if not isinstance(node, ast.ImportFrom):
                    continue
                if not any(alias.name == PLACEHOLDER for alias in node.names):
                    continue
                check_import(node, parent, siblings)
                kept = [
                    alias.name if alias.asname is None else f"{alias.name} as {alias.asname}"
                    for alias in node.names
                    if alias.name != PLACEHOLDER
                ]
                rewrite = f"from {node.module} import {', '.join(kept)}" if kept else ""
                imports[node.lineno] = (node.end_lineno or node.lineno, rewrite)
    return imports


def freeze_file(text: str, target_version: str) -> str:
    imports = placeholder_imports(text)
    columns = comment_columns(text)
    lines = text.splitlines(keepends=True)
    new_lines: list[str] = []
    skip_until = 0

    for lineno, line in enumerate(lines, start=1):
        if lineno <= skip_until:
            continue

        if lineno in imports:
            skip_until, rewrite = imports[lineno]
            if rewrite:
                comments = [
                    lines[n - 1][columns[n] :].rstrip("\r\n")
                    for n in range(lineno, skip_until + 1)
                    if n in columns
                ]
                last = lines[skip_until - 1]
                ending = last[len(last.rstrip("\r\n")) :]
                indent = line[: len(line) - len(line.lstrip())]
                new_lines.append(f"{indent}{'  '.join([rewrite, *comments])}{ending}")
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
    frozen: dict[Path, str] = {}
    for path in Path("src").rglob("*.py"):
        if path in EXCLUDE_PATHS:
            continue

        text = path.read_text()
        if PLACEHOLDER not in text:
            continue

        try:
            frozen[path] = freeze_file(text, target_version)
        except UnsupportedImportError as e:
            sys.exit(f"{path}: {e}")

    for path, text in frozen.items():
        path.write_text(text)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <target_version>")
    freeze_version(sys.argv[1])
