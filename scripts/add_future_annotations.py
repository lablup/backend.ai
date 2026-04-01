#!/usr/bin/env python3
"""
Add 'from __future__ import annotations' to Python files.

This script automatically adds the future annotations import to Python files
that don't already have it. It skips exempted paths like tests, migrations, and stubs.

Usage:
    python scripts/add_future_annotations.py <path>

Where <path> can be:
    - A single Python file
    - A directory (will process all .py files recursively)
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Final

# Paths to skip (relative to project root)
EXEMPT_PATTERNS: Final[list[str]] = [
    "tests/",
    "src/ai/backend/test/",
    "src/ai/backend/manager/models/alembic/",
    "stubs/",
]

FUTURE_IMPORT: Final[str] = "from __future__ import annotations"


def is_exempt(file_path: Path, project_root: Path) -> bool:
    """Check if file should be exempted from processing."""
    relative_path = file_path.relative_to(project_root).as_posix()
    return any(relative_path.startswith(pattern) for pattern in EXEMPT_PATTERNS)


def has_future_annotations(content: str) -> bool:
    """Check if file already has future annotations import."""
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "__future__" and any(
                    alias.name == "annotations" for alias in node.names
                ):
                    return True
    except SyntaxError:
        # If we can't parse, check string content as fallback
        return FUTURE_IMPORT in content
    return False


def get_insertion_point(content: str) -> int:
    """Find the correct insertion point for the future import.

    Returns the line index (0-based) where the import should be inserted.
    Priority:
    1. After shebang (if present)
    2. After encoding declaration (if present)
    3. After module docstring (if present)
    4. Before any other imports or code
    """
    lines = content.splitlines(keepends=True)
    if not lines:
        return 0

    idx = 0

    # Skip shebang
    if lines[idx].startswith("#!"):
        idx += 1

    # Skip encoding declaration
    if idx < len(lines) and re.match(r"#.*coding[:=]", lines[idx]):
        idx += 1

    # Skip module docstring
    try:
        tree = ast.parse(content)
        docstring = ast.get_docstring(tree)
        if docstring:
            # Find where docstring ends
            in_docstring = False
            quote_char = None
            for i in range(idx, len(lines)):
                line = lines[i].strip()
                if not in_docstring:
                    # Check for docstring start
                    if line.startswith('"""') or line.startswith("'''"):
                        quote_char = line[:3]
                        in_docstring = True
                        # Check if it's a single-line docstring
                        if line.count(quote_char) >= 2:
                            idx = i + 1
                            break
                else:
                    # Check for docstring end
                    if quote_char in line:
                        idx = i + 1
                        break
    except SyntaxError:
        pass

    # Skip any blank lines after docstring
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    return idx


def add_future_import(content: str) -> str:
    """Add future annotations import to file content."""
    insertion_idx = get_insertion_point(content)
    lines = content.splitlines(keepends=True)

    # Check if there are already imports at insertion point
    has_imports = insertion_idx < len(lines) and (
        lines[insertion_idx].startswith("import ") or
        lines[insertion_idx].startswith("from ")
    )

    # Build new content
    new_lines = (
        lines[:insertion_idx] +
        [FUTURE_IMPORT + "\n"] +
        (["\n"] if has_imports else []) +
        lines[insertion_idx:]
    )

    return "".join(new_lines)


def process_file(file_path: Path, project_root: Path, dry_run: bool = False) -> bool:
    """Process a single Python file.

    Returns True if file was modified, False otherwise.
    """
    if is_exempt(file_path, project_root):
        return False

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return False

    if has_future_annotations(content):
        return False

    new_content = add_future_import(content)

    if dry_run:
        print(f"Would modify: {file_path.relative_to(project_root)}")
        return True

    try:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"Modified: {file_path.relative_to(project_root)}")
        return True
    except Exception as e:
        print(f"Error writing {file_path}: {e}", file=sys.stderr)
        return False


def process_path(path: Path, project_root: Path, dry_run: bool = False) -> tuple[int, int]:
    """Process a file or directory.

    Returns (files_processed, files_modified) counts.
    """
    files_processed = 0
    files_modified = 0

    if path.is_file():
        if path.suffix == ".py":
            files_processed = 1
            if process_file(path, project_root, dry_run):
                files_modified = 1
    elif path.is_dir():
        for py_file in path.rglob("*.py"):
            files_processed += 1
            if process_file(py_file, project_root, dry_run):
                files_modified += 1
    else:
        print(f"Error: {path} is not a file or directory", file=sys.stderr)
        return (0, 0)

    return (files_processed, files_modified)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add 'from __future__ import annotations' to Python files"
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to Python file or directory to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be modified without making changes",
    )
    args = parser.parse_args()

    # Find project root (directory containing pyproject.toml)
    project_root = Path(__file__).parent.parent.resolve()
    if not (project_root / "pyproject.toml").exists():
        print("Error: Could not find project root (pyproject.toml)", file=sys.stderr)
        return 1

    path = args.path.resolve()
    if not path.exists():
        print(f"Error: {path} does not exist", file=sys.stderr)
        return 1

    print(f"Processing: {path.relative_to(project_root)}")
    if args.dry_run:
        print("DRY RUN - No files will be modified")
    print()

    files_processed, files_modified = process_path(path, project_root, args.dry_run)

    print()
    print(f"Files processed: {files_processed}")
    print(f"Files modified: {files_modified}")
    print(f"Files skipped: {files_processed - files_modified}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
