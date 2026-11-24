#!/usr/bin/env python3
"""Decide which targets each CI job runs and across which shards, without Pants.

    plan-ci-targets.py --base-ref <rev> [--full-run] [--durations <file>] --out <dir>

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

``typecheck.txt``, ``unit.txt`` and ``component.txt`` list file paths, one per line;
``integration.txt`` and ``scenario.txt`` list Pants addresses. A test is a file a ``python_tests`` of its ``BUILD`` owns; its address is
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
- a file a ``BUILD`` target in ``src/`` or ``tests/`` lists in ``dependencies`` to that target's files,
  or, listed in an ``overrides`` entry, to the files that entry names

Changed files that are not Python source:

- ``python.lock``, ``python.lock.metadata``: a full run
- ``pyproject.toml``, ``pants.toml``, a file under ``stubs/``: every ``.py`` is typechecked
- a ``BUILD`` under ``src/``: a full run
- any other file under ``src/`` or ``tests/`` that is not ``.py`` or a ``.md``, ``.rst``
  document (a ``BUILD`` under ``tests/`` included): the ``.py`` files of its directory
  count as changed

A suite gets one shard per ``SHARD_FLOOR`` tests, at most ``SHARD_LIMIT``. Pants assigns
a test of ``integration`` and ``scenario`` to the shard ``crc32(address) % N``. A shard no
test lands in is left out.

The files of ``unit`` and ``component`` go to the shards by run time, longest first, each to
the shard with the smallest total so far. ``--durations`` names the ``test-durations.json``
that ``test-record.yml`` saves, ``{"<suite>": {"<path>": <seconds>}}``. A file it does not
hold counts as the mean of its suite's record; without the option, a missing file or an
empty suite record, every file counts as 1 second. The files of shard ``k`` of ``N`` are
written to ``<suite>.<k>.txt``, which ``ci-pytest.yml`` runs; ``<suite>.txt`` holds all of
them.

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
SHARD_LIMIT = {"unit": 3, "component": 3, "integration": 2, "scenario": 6}
# About a minute of tests on a 4-core runner, the setup every shard pays first.
SHARD_FLOOR = {"unit": 40, "component": 20, "integration": 5, "scenario": 10}
# Suites run by pytest directly, whose spec file lists paths.
PYTEST_SUITES = ("unit", "component")

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
    "files": [],
}


class PlanError(Exception):
    pass


class Target:
    """A ``python_tests``, ``python_test_utils``, ``python_sources`` or ``files`` call of a BUILD."""

    kind: str
    directory: str
    name: str | None
    files: set[str]
    # The files a ``dependencies`` list applies to, with the list: the whole target, and
    # each ``overrides`` entry for the files it names.
    dep_groups: list[tuple[set[str], list[str]]]

    def __init__(
        self,
        kind: str,
        directory: str,
        name: str | None,
        files: set[str],
        dep_groups: list[tuple[set[str], list[str]]],
    ) -> None:
        self.kind = kind
        self.directory = directory
        self.name = name
        self.files = files
        self.dep_groups = dep_groups

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


def qualify(dep: str, directory: str) -> str:
    """Write the ``:name`` address of a BUILD with the directory in front."""
    return f"{directory}{dep}" if dep.startswith(":") else dep


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
        overrides = literal(call, "overrides", {}, where)
        if not isinstance(sources, list) or not isinstance(deps, list):
            raise PlanError(f"{where}: `sources` and `dependencies` must be lists")
        if not isinstance(overrides, dict):
            raise PlanError(f"{where}: `overrides` must be a dict")
        files = {f for f in matching_files(root, directory, sources) if is_py(f)}
        groups = [(files, [qualify(d, directory) for d in deps])]
        for key, value in overrides.items():
            override_deps = value.get("dependencies", []) if isinstance(value, dict) else []
            keys = [key] if isinstance(key, str) else list(key)
            named = matching_files(root, directory, keys) & files
            groups.append((named, [qualify(d, directory) for d in override_deps]))
        targets.append(Target(kind, directory, name, files, groups))
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

    An address that names no ``python_*`` or ``files`` target of a BUILD (a resource, a
    requirement) names no files.
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
        for owners, deps in target.dep_groups:
            for dep in deps:
                generator, files = dependency_files(dep, every, targets)
                for f in files:
                    if generator is None:
                        edges.setdefault(f, set()).update(owners)
                    else:
                        edges.setdefault(f, set()).add(generator)
                if generator is not None and files:
                    edges.setdefault(generator, set()).update(owners)
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


def shard_count(tests: list[str], limit: int, floor: int) -> int:
    return min(limit, math.ceil(len(tests) / floor)) if tests else 0


def plan_shards(tests: list[str], limit: int, floor: int) -> list[str]:
    count = shard_count(tests, limit, floor)
    filled = sorted({zlib.crc32(t.encode()) % count for t in tests})
    return [f"{k}/{count}" for k in filled]


def read_durations(path: pathlib.Path | None) -> dict[str, dict[str, float]]:
    """The seconds per file of each suite; empty when there is no record."""
    if path is None or not path.is_file():
        return {}
    raw = json.loads(path.read_text())
    return {suite: dict(raw.get(suite, {})) for suite in PYTEST_SUITES}


def assign_by_duration(
    files: list[str], count: int, durations: dict[str, float]
) -> list[list[str]]:
    """Longest file first, each to the shard with the smallest total so far."""
    mean = sum(durations.values()) / len(durations) if durations else 1.0
    weight = {f: durations.get(f, mean) for f in files}
    shards: list[list[str]] = [[] for _ in range(count)]
    totals = [0.0] * count
    for f in sorted(files, key=lambda f: (-weight[f], f)):
        k = min(range(count), key=lambda i: (totals[i], i))
        shards[k].append(f)
        totals[k] += weight[f]
    return [sorted(s) for s in shards]


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
        "--durations",
        type=pathlib.Path,
        help="the test-durations.json to assign the unit and component files by",
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
        addresses[suite] = (
            files[suite] if suite in PYTEST_SUITES else [owners[f].address(f) for f in files[suite]]
        )

    args.out.mkdir(parents=True, exist_ok=True)
    for name, lines in addresses.items():
        (args.out / f"{name}.txt").write_text("".join(f"{line}\n" for line in lines))

    durations = read_durations(args.durations)
    sys.stdout.write(f"typecheck={'true' if addresses['typecheck'] else 'false'}\n")
    for suite in SUITES:
        if suite in PYTEST_SUITES:
            count = shard_count(addresses[suite], SHARD_LIMIT[suite], SHARD_FLOOR[suite])
            assigned = assign_by_duration(addresses[suite], count, durations.get(suite, {}))
            shards = []
            for k, shard_files in enumerate(assigned):
                if shard_files:
                    (args.out / f"{suite}.{k}.txt").write_text(
                        "".join(f"{f}\n" for f in shard_files)
                    )
                    shards.append(f"{k}/{count}")
        else:
            shards = (
                plan_shards(addresses[suite], SHARD_LIMIT[suite], SHARD_FLOOR[suite])
                if addresses[suite]
                else []
            )
        sys.stdout.write(f"{suite}-shards={json.dumps(shards, separators=(',', ':'))}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PlanError as e:
        sys.stderr.write(f"error: {e}\n")
        sys.exit(1)
