"""Fail when an `__init__.py` under the given directories imports anything.

Usage: python scripts/check-init-imports.py <dir>...

Prints each offending file and exits 1. The files in `ALLOWED` hold code and keep their imports.
"""

import ast
import sys
from pathlib import Path

ALLOWED = frozenset({
    "src/ai/backend/manager/__init__.py",
    "src/ai/backend/manager/actions/monitors/__init__.py",
    "src/ai/backend/manager/actions/validators/rbac/__init__.py",
    "src/ai/backend/manager/models/login_session/__init__.py",
    "src/ai/backend/manager/models/minilang/__init__.py",
    "src/ai/backend/manager/models/rbac/__init__.py",
})


def find_imports(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(), filename=str(path))
    return [
        node.lineno for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
    ]


def main(roots: list[str]) -> int:
    if not roots:
        print(__doc__, file=sys.stderr)
        return 2
    failed = False
    for root in roots:
        for path in sorted(Path(root).rglob("__init__.py")):
            if path.as_posix() in ALLOWED:
                continue
            for lineno in find_imports(path):
                print(f"{path}:{lineno}: import in __init__.py; import from the defining module")
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
