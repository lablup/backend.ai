#!/usr/bin/env python3
"""Decide which targets each CI job runs and across which shards, without Pants.

    plan-ci-targets.py --base-ref <rev> [--full-run] --out <dir>

Writes one spec file per job into <dir> and prints ``KEY=value`` lines for a job
output:

=================== ================================================================
Key                 Value
=================== ================================================================
``typecheck``       ``true`` when ``typecheck.txt`` holds any target
``<suite>-shards``  The ``--shard`` values whose shard holds a target in
                    ``<suite>.txt``, as a JSON list; ``[]`` when the suite has none
=================== ================================================================

========================= ================================================== ==========
Spec file                 Changed-only run (against <rev>)                    Full run
========================= ================================================== ==========
``typecheck.txt``         the ``.py`` files, transitive dependents            every
                                                                              ``.py``
``unit.txt``              ``tests/unit/`` tests, direct dependents            the suite
``component.txt``         ``tests/component/`` tests, direct dependents       the suite
``integration.txt``       ``tests/integration/`` tests, no dependents         the suite
``scenario.txt``          tests of every scenario component a transitive      the suite
                          dependent falls in, plus the setup
========================= ================================================== ==========

``typecheck.txt`` lists file paths and the other files list Pants addresses, one per
line. A test is a file a ``python_tests`` of its ``BUILD`` owns; its address is
``<file>:<name>``, or ``<file>`` when the target has no name.

The changed files are ``git diff --name-only <rev>``. The dependents come from
``ruff analyze graph --direction dependents src tests stubs`` (``RUFF_GRAPH_VERSION``),
which holds the import edges only (``--isolated``, so the ``[tool.ruff]`` excludes of
``pyproject.toml`` do not drop a directory such as ``plugins``); the ``.pyi`` files of
``stubs/`` are nodes of it. The nodes must equal the ``.py`` and ``.pyi`` files that
``git ls-files src tests stubs`` lists, or the script fails and prints the difference.
A full typecheck lists those tracked files.
The graph gets the edges Pants adds on top of import inference:

- a non-empty ``__init__.py`` to every module under it
- a ``conftest.py`` to every test under it
- a file a ``BUILD`` target in ``src/`` or ``tests/`` lists in ``dependencies`` to that target's files

Changed files that are not Python source:

- ``python.lock``, ``python.lock.metadata``: a full run
- ``pyproject.toml``, ``pants.toml``, a file under ``stubs/``: every ``.py`` is typechecked
- a ``BUILD`` under ``src/``: a full run
- any other file under ``src/`` or ``tests/`` that is not ``.py`` or a ``.md``, ``.rst``
  document (a ``BUILD`` under ``tests/`` included): the ``.py`` files of its directory
  count as changed

A suite gets one shard per ``SHARD_FLOOR`` tests, at most ``SHARD_LIMIT``. Pants
assigns a test to ``crc32(address) % N``, so a shard no test lands in is left out.

Run it from the repository root with ``uv`` on the path:

    .github/scripts/plan-ci-targets.py --base-ref HEAD~1 --out dist/ci-targets
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import pathlib
import re
import subprocess
import sys
import zlib
from collections.abc import Iterable

RUFF_GRAPH_VERSION = "0.17.5"
RUFF_GRAPH_CONFIG = 'src = ["src", "tests/scenario", "stubs", "."]'

SUITES = ("unit", "component", "integration", "scenario")
SHARD_LIMIT = {"unit": 6, "component": 6, "integration": 2, "scenario": 6}
# About a minute of tests on a 4-core runner, the setup every shard pays first.
# component: two batches of the `batch_size` 5 in pants.toml.
SHARD_FLOOR = {"unit": 20, "component": 10, "integration": 5, "scenario": 10}

SCENARIO_SETUP = "tests/scenario/bai_scenario/setup"
SCENARIO_COMPONENT = re.compile(r"^tests/scenario/bai_scenario/manager/([^/]+)/")

FULL_RUN_FILES = {"python.lock", "python.lock.metadata"}
TYPECHECK_ALL_FILES = {"pyproject.toml", "pants.toml"}
TYPECHECK_ALL_DIRS = ("stubs/",)
DOC_SUFFIXES = (".md", ".rst")

DEFAULT_SOURCES = {
    "python_tests": ["test_*.py", "*_test.py", "tests.py"],
    "python_test_utils": ["conftest.py"],
    "python_sources": ["*.py", "!test_*.py", "!*_test.py", "!tests.py", "!conftest.py"],
}


class PlanError(Exception):
    pass


class Target:
    """A ``python_tests``, ``python_test_utils`` or ``python_sources`` call of a BUILD."""

    def __init__(
        self, kind: str, directory: str, name: str | None, files: set[str], deps: list[str]
    ) -> None:
        self.kind = kind
        self.directory = directory
        self.name = name
        self.files = files
        self.deps = deps

    def address(self, file: str) -> str:
        return file if self.name is None else f"{file}:{self.name}"


def parent(path: str) -> str:
    return pathlib.PurePosixPath(path).parent.as_posix()


def is_py(path: str) -> bool:
    return path.endswith(".py")


def is_source(path: str) -> bool:
    return path.endswith((".py", ".pyi"))


def under(files: Iterable[str], directory: str) -> set[str]:
    return {f for f in files if f.startswith(f"{directory}/")}


def literal(call: ast.Call, key: str, default: object, where: str) -> object:
    for keyword in call.keywords:
        if keyword.arg == key:
            try:
                return ast.literal_eval(keyword.value)
            except ValueError as e:
                raise PlanError(f"{where}: `{key}` is not a literal") from e
    return default


def matching_files(root: pathlib.Path, directory: str, patterns: list[str]) -> set[str]:
    base = root / directory
    included: set[str] = set()
    excluded: set[str] = set()
    for pattern in patterns:
        negate = pattern.startswith("!")
        matched = {
            p.relative_to(root).as_posix()
            for p in base.glob(pattern.removeprefix("!"))
            if p.is_file()
        }
        (excluded if negate else included).update(matched)
    return included - excluded


def parse_build(root: pathlib.Path, build: pathlib.Path) -> list[Target]:
    directory = build.parent.relative_to(root).as_posix()
    where = build.relative_to(root).as_posix()
    targets: list[Target] = []
    for node in ast.parse(build.read_text(), filename=where).body:
        if not (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id in DEFAULT_SOURCES
        ):
            continue
        call = node.value
        kind = node.value.func.id
        name = literal(call, "name", None, where)
        sources = literal(call, "sources", DEFAULT_SOURCES[kind], where)
        deps = literal(call, "dependencies", [], where)
        if not isinstance(sources, list) or not isinstance(deps, list):
            raise PlanError(f"{where}: `sources` and `dependencies` must be lists")
        files = {f for f in matching_files(root, directory, sources) if is_py(f)}
        targets.append(Target(kind, directory, name, files, deps))
    return targets


def load_targets(root: pathlib.Path) -> list[Target]:
    targets: list[Target] = []
    for build in sorted([*(root / "src").rglob("BUILD"), *(root / "tests").rglob("BUILD")]):
        targets.extend(parse_build(root, build))
    return targets


def map_test_owners(targets: list[Target]) -> dict[str, Target]:
    """Map each test file to its ``python_tests``; an overlap is an error."""
    owners: dict[str, Target] = {}
    for target in targets:
        if target.kind != "python_tests":
            continue
        for f in sorted(target.files):
            if f in owners:
                raise PlanError(
                    f"{f} belongs to two python_tests: {owners[f].address(f)} and {target.address(f)}"
                )
            owners[f] = target
    return owners


def dependency_files(
    dep: str, every: set[str], targets: list[Target]
) -> tuple[str | None, set[str]]:
    """The files a ``dependencies`` entry names, and the target it names when it is a generator.

    An address that names no ``python_*`` target of a BUILD (a resource, a requirement)
    names no files.
    """
    if dep.startswith(("//", "!")):
        return None, set()
    path, _, name = dep.partition(":")
    if path.endswith(".py"):
        return None, {path} & every
    name = name or pathlib.PurePosixPath(path).name
    named = [t for t in targets if t.directory == path and t.name in (name, None)]
    if t_files := set().union(*(t.files for t in named)) & every:
        return dep, t_files
    return None, set()


def build_edges(every: set[str], targets: list[Target]) -> dict[str, set[str]]:
    """Map a dependency named in a tests/ BUILD to the files of the target naming it.

    A file listed by path is a direct dependency. A target listed by address is a
    generator: its files lead to the target, and the target leads to the files that list
    it, so those files are dependents of the second degree, as Pants counts them.
    """
    edges: dict[str, set[str]] = {}
    for target in targets:
        for dep in target.deps:
            generator, files = dependency_files(dep, every, targets)
            for f in files:
                if generator is None:
                    edges.setdefault(f, set()).update(target.files)
                else:
                    edges.setdefault(f, set()).add(generator)
            if generator is not None and files:
                edges.setdefault(generator, set()).update(target.files)
    return edges


def ruff_graph() -> dict[str, set[str]]:
    result = subprocess.run(
        [
            "uvx",
            f"ruff@{RUFF_GRAPH_VERSION}",
            "analyze",
            "graph",
            "--isolated",
            "--direction",
            "dependents",
            "--config",
            RUFF_GRAPH_CONFIG,
            "src",
            "tests",
            "stubs",
        ],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    raw = json.loads(result.stdout)
    return {k: {d for d in v if is_source(d)} for k, v in raw.items() if is_source(k)}


def tracked_sources() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "src", "tests", "stubs"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return {f for f in result.stdout.splitlines() if is_source(f)}


def add_pants_edges(
    graph: dict[str, set[str]], root: pathlib.Path, targets: list[Target], tests: set[str]
) -> None:
    every = set(graph)
    for f in sorted(every):
        name = pathlib.PurePosixPath(f).name
        if name == "__init__.py" and (root / f).read_text().strip():
            graph[f] |= under(every, parent(f)) - {f}
        elif name == "conftest.py":
            graph[f] |= under(tests, parent(f))
    for f, owners in build_edges(every, targets).items():
        graph.setdefault(f, set()).update(owners)


def dependents(graph: dict[str, set[str]], files: set[str]) -> tuple[set[str], set[str]]:
    direct = set(files)
    for f in files:
        direct |= graph[f]
    transitive = set(direct)
    queue = list(direct)
    while queue:
        for d in graph.get(queue.pop(), set()):
            if d not in transitive:
                transitive.add(d)
                queue.append(d)
    return direct, transitive


def changed_files(base_ref: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref], check=True, stdout=subprocess.PIPE, text=True
    )
    return result.stdout.splitlines()


def changed_sources(changed: list[str], every: set[str]) -> set[str]:
    """The ``.py`` files of the graph that the changed files stand for."""
    files = {f for f in changed if f in every}
    for f in changed:
        if f.startswith(("src/", "tests/")) and not is_py(f) and not f.endswith(DOC_SUFFIXES):
            files |= {s for s in every if parent(s) == parent(f)}
    return files


def in_suite(files: Iterable[str], suite: str) -> list[str]:
    return sorted(f for f in files if f.startswith(f"tests/{suite}/"))


def scenario_tests(transitive: set[str], tests: Iterable[str]) -> list[str]:
    # A component runs whole or not at all: its report.md covers every scenario it
    # holds. Selection is transitive, because a scenario reaches src through its seeds.
    touched = in_suite(transitive, "scenario")
    if not touched:
        return []
    components = sorted({m[1] for f in touched if (m := SCENARIO_COMPONENT.match(f))})
    directories = [
        SCENARIO_SETUP,
        *(f"tests/scenario/bai_scenario/manager/{c}" for c in components),
    ]
    return sorted(f for f in tests if any(f.startswith(f"{d}/") for d in directories))


def plan_shards(tests: list[str], limit: int, floor: int) -> list[str]:
    if not tests:
        return []
    count = min(limit, math.ceil(len(tests) / floor))
    filled = sorted({zlib.crc32(t.encode()) % count for t in tests})
    return [f"{k}/{count}" for k in filled]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--base-ref", required=True, help="the revision a changed-only run compares against"
    )
    parser.add_argument(
        "--full-run", action="store_true", help="run every test instead of the changed ones"
    )
    parser.add_argument(
        "--out", required=True, type=pathlib.Path, help="the directory to write the spec files into"
    )
    args = parser.parse_args()
    root = pathlib.Path()

    targets = load_targets(root)
    owners = map_test_owners(targets)
    tests = set(owners)
    graph = ruff_graph()
    every = set(graph)
    tracked = tracked_sources()
    if every != tracked:
        missing = sorted(tracked - every)
        extra = sorted(every - tracked)
        raise PlanError(
            f"the ruff graph and `git ls-files` differ: {len(missing)} files missing from the "
            f"graph {missing[:20]}, {len(extra)} not tracked {extra[:20]}"
        )
    add_pants_edges(graph, root, targets, tests)

    changed = changed_files(args.base_ref)
    full_run = args.full_run or any(
        f in FULL_RUN_FILES or (f.startswith("src/") and pathlib.PurePosixPath(f).name == "BUILD")
        for f in changed
    )
    typecheck_all = full_run or any(
        f in TYPECHECK_ALL_FILES or f.startswith(TYPECHECK_ALL_DIRS) for f in changed
    )

    sources = changed_sources(changed, every)
    direct, transitive = dependents(graph, sources)
    files: dict[str, list[str]] = {
        "typecheck": sorted(f for f in (tracked if typecheck_all else transitive) if is_py(f))
    }
    if full_run:
        for suite in SUITES:
            files[suite] = in_suite(tests, suite)
    else:
        files["unit"] = in_suite(direct & tests, "unit")
        files["component"] = in_suite(direct & tests, "component")
        files["integration"] = in_suite(sources & tests, "integration")
        files["scenario"] = scenario_tests(transitive, tests)

    addresses = {"typecheck": files["typecheck"]}
    for suite in SUITES:
        addresses[suite] = [owners[f].address(f) for f in files[suite]]

    args.out.mkdir(parents=True, exist_ok=True)
    for name, lines in addresses.items():
        (args.out / f"{name}.txt").write_text("".join(f"{line}\n" for line in lines))

    sys.stdout.write(f"typecheck={'true' if addresses['typecheck'] else 'false'}\n")
    for suite in SUITES:
        shards = plan_shards(addresses[suite], SHARD_LIMIT[suite], SHARD_FLOOR[suite])
        sys.stdout.write(f"{suite}-shards={json.dumps(shards, separators=(',', ':'))}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PlanError as e:
        sys.stderr.write(f"error: {e}\n")
        sys.exit(1)
