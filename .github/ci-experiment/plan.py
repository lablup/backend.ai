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

The graph gets the edges Pants adds on top of import inference:

- a non-empty ``__init__.py`` to every module under it
- a ``conftest.py`` to every test under it
- a file a ``tests/`` BUILD target lists in ``dependencies`` to that target's files
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

TEST_NAME = re.compile(r"(^test_.*\.py$)|(.*_test\.py$)|(^tests\.py$)")
TARGET = re.compile(r"\b(python_tests|python_test_utils)\(")
DEPENDENCY = re.compile(r'"([^"]+)"')


def is_test(path: str) -> bool:
    return TEST_NAME.match(pathlib.PurePosixPath(path).name) is not None


def parent(path: str) -> str:
    return pathlib.PurePosixPath(path).parent.as_posix()


def under(files: set[str], directory: str) -> set[str]:
    return {f for f in files if f.startswith(f"{directory}/")}


def dependency_files(dep: str, every: set[str], by_parent: dict[str, set[str]]) -> set[str]:
    target, _, name = dep.partition(":")
    if target.endswith(".py"):
        return {target} & every
    if name in ("", "src"):
        # The `python_sources` of a directory: its own files, not its subdirectories.
        return by_parent.get(target, set())
    return under(every, target)


def build_edges(root: pathlib.Path, every: set[str]) -> dict[str, set[str]]:
    """Map a dependency named in a tests/ BUILD to the files of the target naming it."""
    edges: dict[str, set[str]] = {}
    by_parent: dict[str, set[str]] = {}
    for f in every:
        by_parent.setdefault(parent(f), set()).add(f)
    for build in sorted((root / "tests").rglob("BUILD")):
        directory = build.parent.relative_to(root).as_posix()
        own = by_parent.get(directory, set())
        text = build.read_text()
        calls = list(TARGET.finditer(text))
        for i, call in enumerate(calls):
            body = text[call.end() : calls[i + 1].start() if i + 1 < len(calls) else len(text)]
            start = body.find("dependencies")
            if start < 0:
                continue
            block = body[start : body.find("]", start)]
            deps = [d for d in DEPENDENCY.findall(block) if not d.startswith("//")]
            owners = {f for f in own if is_test(f) == (call.group(1) == "python_tests")}
            for dep in deps:
                for path in dependency_files(dep, every, by_parent):
                    edges.setdefault(path, set()).update(owners)
    return edges


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--graph", required=True, type=pathlib.Path)
    parser.add_argument("--changed", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--root", default=pathlib.Path(), type=pathlib.Path)
    args = parser.parse_args()

    graph = {k: set(v) for k, v in json.loads(args.graph.read_text()).items()}
    every = set(graph)
    for f in every:
        name = pathlib.PurePosixPath(f).name
        if name == "__init__.py" and (args.root / f).read_text().strip():
            graph[f] |= under(every, parent(f)) - {f}
        elif name == "conftest.py":
            graph[f] |= {t for t in under(every, parent(f)) if is_test(t)}
    for f, owners in build_edges(args.root, every).items():
        graph[f] |= owners

    changed = {line.strip() for line in args.changed.read_text().splitlines() if line.strip()}
    changed_py = changed & every
    direct = set(changed_py)
    for c in changed_py:
        direct |= graph[c]
    transitive = set(direct)
    queue = list(direct)
    while queue:
        for d in graph.get(queue.pop(), set()):
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
