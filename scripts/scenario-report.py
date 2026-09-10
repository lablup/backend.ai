#!/usr/bin/env python3
"""Turn the lines a scenario run wrote into a report grouped by domain and behaviour.

Each scenario appends one JSON line to the file named by ``BACKEND_SCENARIO_LOG`` while
the tests run. Pants gives every test file its own process and every shard its own
machine, so the lines arrive interleaved and possibly in several files; this merges them
and prints what each domain now covers.

    BACKEND_SCENARIO_LOG=dist/scenarios.jsonl pants test tests/scenario::
    python scripts/scenario-report.py dist/scenarios.jsonl > dist/scenarios.md
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import Any

MARK = {"passed": "pass", "failed": "FAIL", "skipped": "skip"}


def rows_of(paths: Sequence[pathlib.Path]) -> list[dict[str, Any]]:
    """Every line the run wrote, with duplicates from a retried attempt dropped."""
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for path in paths:
        for line in path.read_text(encoding="utf8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            # A retry writes the row again; the last word on a scenario wins.
            seen[(row["module"], row["summary"])] = row
    return list(seen.values())


def domain_of(module: str) -> str:
    """The domain a module belongs to, read off its package path."""
    parts = module.split(".")
    return parts[-2] if len(parts) >= 2 else module


def behaviour_of(module: str) -> str:
    """The behaviour a module covers, read off its file name."""
    name = module.split(".")[-1]
    return name.removeprefix("test_")


def unexercised(rows: Iterable[dict[str, Any]]) -> list[str]:
    """Adapter calls the run never made.

    The kit reads what the adapter offers off the class, so this is the gap between the
    component's surface and the table, not between the table and a hand-kept list.
    """
    offered: set[str] = set()
    called: set[str] = set()
    for row in rows:
        offered.update(row.get("offers", ()))
        called.add(row["operation"])
    return sorted(offered - called)


def render(rows: Iterable[dict[str, Any]]) -> str:
    by_domain: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        by_domain[domain_of(row["module"])][behaviour_of(row["module"])].append(row)

    total = sum(len(rs) for bs in by_domain.values() for rs in bs.values())
    failed = sum(
        1 for bs in by_domain.values() for rs in bs.values() for r in rs if r["outcome"] == "failed"
    )

    out: list[str] = ["# Scenario coverage", ""]
    out.append(f"{total} scenarios over {len(by_domain)} domains, {failed} failing.")
    out.append("")

    out.append("| domain | scenarios | behaviours | failing |")
    out.append("|---|---:|---|---:|")
    for domain in sorted(by_domain):
        behaviours = by_domain[domain]
        count = sum(len(rs) for rs in behaviours.values())
        bad = sum(1 for rs in behaviours.values() for r in rs if r["outcome"] == "failed")
        out.append(f"| {domain} | {count} | {', '.join(sorted(behaviours))} | {bad} |")
    out.append("")

    for domain in sorted(by_domain):
        out.append(f"## {domain}")
        out.append("")
        untouched = unexercised(r for bs in [by_domain[domain]] for rs in bs.values() for r in rs)
        if untouched:
            out.append(f"Not exercised by any scenario: {', '.join(untouched)}.")
            out.append("")
        for behaviour in sorted(by_domain[domain]):
            rows_here = sorted(by_domain[domain][behaviour], key=lambda r: r["summary"])
            out.append(f"### {behaviour}")
            out.append("")
            for row in rows_here:
                mark = MARK.get(row["outcome"], row["outcome"])
                out.append(f"#### {row['summary']} — {mark}")
                out.append("")
                out.append(row.get("description", ""))
                out.append("")
                for i, step in enumerate(row.get("steps", ()), start=1):
                    out.append(f"{i}. {step}")
                situation = " ".join(row.get("situation", ()))
                out.append(f"{len(row.get('steps', ())) + 1}. calls {row['operation']}")
                answers = row["expects"] + (f", with {situation} overridden" if situation else "")
                out.append(f"{len(row.get('steps', ())) + 2}. {answers}")
                out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=pathlib.Path, help="the JSONL files a run wrote")
    args = parser.parse_args()
    missing = [p for p in args.logs if not p.exists()]
    if missing:
        print(f"no such log: {', '.join(str(p) for p in missing)}", file=sys.stderr)
        return 1
    print(render(rows_of(args.logs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
