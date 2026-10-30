#!/usr/bin/env python3
"""Decide which targets each CI job runs and across which shards.

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
``typecheck.txt``         every target, transitive dependents                 same
``unit.txt``              ``tests/unit/`` tests, direct dependents            the suite
``component.txt``         ``tests/component/`` tests, direct dependents       the suite
``integration.txt``       ``tests/integration/`` tests, no dependents         the suite
``scenario.txt``          tests of every scenario component a transitive      the suite
                          dependent falls in, plus the setup
========================= ================================================== ==========

A suite gets one shard per ``SHARD_FLOOR`` tests, at most ``SHARD_LIMIT``. Pants
assigns a test to ``crc32(address) % N``, so a shard no test lands in is left out.

Run it from the repository root with Pants on the path:

    .github/scripts/plan-ci-targets.py --base-ref HEAD~1 --out dist/ci-targets
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import subprocess
import sys
import zlib

SUITES = ("unit", "component", "integration", "scenario")
SHARD_LIMIT = {"unit": 6, "component": 6, "integration": 2, "scenario": 6}
# About a minute of tests on a 4-core runner, the setup every shard pays first.
# component: two batches of the `batch_size` 5 in pants.toml.
SHARD_FLOOR = {"unit": 20, "component": 10, "integration": 5, "scenario": 10}

SCENARIO_SETUP = "tests/scenario/bai_scenario/setup::"
SCENARIO_COMPONENT = re.compile(r"^tests/scenario/bai_scenario/manager/([^/]+)/")


def pants_list(*args: str) -> list[str]:
    result = subprocess.run(["pants", *args, "list"], check=True, stdout=subprocess.PIPE, text=True)
    return result.stdout.split()


def list_tests(*args: str) -> list[str]:
    return pants_list("--filter-target-type=python_test", *args)


def in_suite(addresses: list[str], suite: str) -> list[str]:
    return [a for a in addresses if a.startswith(f"tests/{suite}/")]


def scenario_specs(transitive: list[str]) -> list[str]:
    # A component runs whole or not at all: its report.md covers every scenario it
    # holds. Selection is transitive, because a scenario reaches src through its seeds.
    touched = in_suite(transitive, "scenario")
    if not touched:
        return []
    components = sorted({m[1] for a in touched if (m := SCENARIO_COMPONENT.match(a))})
    return [SCENARIO_SETUP, *(f"tests/scenario/bai_scenario/manager/{c}::" for c in components)]


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

    changed = f"--changed-since={args.base_ref}"
    # Only the dependents runs build the dependents map, and the direct run reuses it
    # while pantsd stays under `pantsd_max_memory_usage`.
    has_changes = bool(pants_list(changed))
    transitive = pants_list(changed, "--changed-dependents=transitive") if has_changes else []
    targets: dict[str, list[str]] = {"typecheck": transitive}
    if args.full_run:
        every = list_tests(*(f"tests/{s}::" for s in SUITES))
        for suite in SUITES:
            targets[suite] = in_suite(every, suite)
    else:
        direct = list_tests(changed, "--changed-dependents=direct") if has_changes else []
        targets["unit"] = in_suite(direct, "unit")
        targets["component"] = in_suite(direct, "component")
        targets["integration"] = in_suite(list_tests(changed), "integration")
        specs = scenario_specs(transitive)
        targets["scenario"] = list_tests(*specs) if specs else []

    args.out.mkdir(parents=True, exist_ok=True)
    for name, addresses in targets.items():
        (args.out / f"{name}.txt").write_text("".join(f"{a}\n" for a in addresses))

    sys.stdout.write(f"typecheck={'true' if transitive else 'false'}\n")
    for suite in SUITES:
        shards = plan_shards(targets[suite], SHARD_LIMIT[suite], SHARD_FLOOR[suite])
        sys.stdout.write(f"{suite}-shards={json.dumps(shards, separators=(',', ':'))}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
