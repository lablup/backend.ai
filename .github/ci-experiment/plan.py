#!/usr/bin/env python3
"""Pick the unit, component and typecheck files a change affects, without Pants.

    plan.py --graph <ruff-dependents.json> --changed <file-list> --out <dir>

``<ruff-dependents.json>`` is the output of
``ruff analyze graph --direction dependents src tests``: each file mapped to the
files importing it. Writes ``unit.txt``, ``component.txt`` and ``typecheck.txt``
(one path per line) into ``<dir>`` and prints ``KEY=count`` lines.

============== =========================================================
File           Selection
============== =========================================================
unit.txt       ``tests/unit/`` test files among the direct dependents
component.txt  ``tests/component/`` test files among the direct dependents
typecheck.txt  ``.py`` files among the transitive dependents
============== =========================================================

The direct dependents of a changed file are its importers plus what Pants adds
on top of import inference:

- every module under a changed non-empty ``__init__.py``
- every test under a changed ``conftest.py``
- the tests of a ``BUILD`` whose explicit ``dependencies`` name a changed file
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

TEST_NAME = re.compile(r"(^test_.*\.py$)|(.*_test\.py$)|(^tests\.py$)")
DEPENDENCY = re.compile(r'"([^"]+)"')


def is_test(path: str) -> bool:
    return TEST_NAME.match(pathlib.PurePosixPath(path).name) is not None


def files_under(files: set[str], directory: str) -> set[str]:
    prefix = f"{directory}/" if directory else ""
    return {f for f in files if f.startswith(prefix)}


def build_dependency_owners(root: pathlib.Path) -> dict[str, list[str]]:
    """Map each test directory to the paths its BUILD lists in `dependencies`."""
    owners: dict[str, list[str]] = {}
    for build in sorted((root / "tests").rglob("BUILD")):
        text = build.read_text()
        start = text.find("dependencies")
        if start < 0:
            continue
        block = text[start : text.find("]", start)]
        deps = [d for d in DEPENDENCY.findall(block) if not d.startswith("//")]
        if deps:
            owners[build.parent.relative_to(root).as_posix()] = deps
    return owners


def dependency_matches(dep: str, changed: str) -> bool:
    path, _, name = dep.partition(":")
    if path.endswith(".py"):
        return changed == path
    if name in ("", "src"):
        # The `python_sources` of a directory: its own files, not its subdirectories.
        return pathlib.PurePosixPath(changed).parent.as_posix() == path
    return changed.startswith(f"{path}/")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--graph", required=True, type=pathlib.Path)
    parser.add_argument("--changed", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--root", default=pathlib.Path(), type=pathlib.Path)
    args = parser.parse_args()

    graph: dict[str, list[str]] = json.loads(args.graph.read_text())
    every = set(graph)
    changed = {line.strip() for line in args.changed.read_text().splitlines() if line.strip()}
    changed_py = {c for c in changed if c in every}

    direct = set(changed_py)
    for c in changed_py:
        direct.update(graph[c])
        name = pathlib.PurePosixPath(c).name
        if name == "__init__.py" and (args.root / c).read_text().strip():
            direct |= files_under(every, pathlib.PurePosixPath(c).parent.as_posix())
    for f in changed_py:
        if pathlib.PurePosixPath(f).name == "conftest.py":
            direct |= {
                t
                for t in files_under(every, pathlib.PurePosixPath(f).parent.as_posix())
                if is_test(t)
            }
    for test_dir, deps in build_dependency_owners(args.root).items():
        if any(dependency_matches(d, c) for d in deps for c in changed):
            direct |= {
                t
                for t in every
                if pathlib.PurePosixPath(t).parent.as_posix() == test_dir and is_test(t)
            }

    transitive = set(direct)
    queue = list(direct)
    while queue:
        for d in graph.get(queue.pop(), []):
            if d not in transitive:
                transitive.add(d)
                queue.append(d)

    selected = {
        "unit": sorted(f for f in direct if f.startswith("tests/unit/") and is_test(f)),
        "component": sorted(f for f in direct if f.startswith("tests/component/") and is_test(f)),
        "typecheck": sorted(transitive),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    for name, files in selected.items():
        (args.out / f"{name}.txt").write_text("".join(f"{f}\n" for f in files))
        sys.stdout.write(f"{name}={len(files)}\n")
    sys.stdout.write(f"changed-py={len(changed_py)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
