#!/usr/bin/env python3
"""Turn the lines a scenario run wrote into a report grouped by domain and behaviour.

Each scenario appends one JSON line to the file named by ``BACKEND_SCENARIO_LOG`` while
the tests run. Pants gives every test file its own process and every shard its own
machine, so the lines arrive interleaved and possibly in several files; this merges them
and prints what each domain now covers.

    BACKEND_SCENARIO_LOG=dist/scenarios.jsonl pants test tests/scenario::
    python scripts/scenario-report.py dist/scenarios.jsonl > dist/scenarios.md
    python scripts/scenario-report.py dist/scenarios.jsonl --format json > dist/scenarios.json

``--format json`` answers the same report as data, for a tool that wants to read it
rather than a person. ``--format summary`` answers the counts alone.
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
    out.append(f"{total} scenarios over {len(by_domain)} components, {failed} failing.")
    out.append("")

    out.append("| component | scenarios | behaviours | failing |")
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
                actor = row.get("actor", "")
                for i, step in enumerate(row.get("steps", ()), start=1):
                    mark = "  ← the actor" if step and step == actor else ""
                    out.append(f"{i}. {step}{mark}")
                situation = " ".join(row.get("situation", ()))
                out.append(f"{len(row.get('steps', ())) + 1}. calls {row['operation']}")
                answers = row["expects"] + (f", with {situation} overridden" if situation else "")
                out.append(f"{len(row.get('steps', ())) + 2}. {answers}")
                out.append("")
    return "\n".join(out)


def as_data(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """The same report as data: what each domain covers, and what it does not."""
    by_domain: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        by_domain[domain_of(row["module"])][behaviour_of(row["module"])].append(row)

    domains = []
    for domain in sorted(by_domain):
        behaviours = by_domain[domain]
        every = [r for rs in behaviours.values() for r in rs]
        domains.append({
            "domain": domain,
            "adapter": next((r.get("adapter", "") for r in every if r.get("adapter")), ""),
            "scenarios": len(every),
            "failing": sum(1 for r in every if r["outcome"] == "failed"),
            "unexercised": unexercised(every),
            "behaviours": [
                {
                    "behaviour": behaviour,
                    "rows": [
                        {
                            "summary": row["summary"],
                            "description": row.get("description", ""),
                            "actor": row.get("actor", ""),
                            "outcome": row["outcome"],
                            "steps": list(row.get("steps", ())),
                            "calls": row["operation"],
                            "expects": row["expects"],
                            "overrides": sorted(row.get("situation", ())),
                        }
                        for row in sorted(behaviours[behaviour], key=lambda r: r["summary"])
                    ],
                }
                for behaviour in sorted(behaviours)
            ],
        })

    every_row = [r for bs in by_domain.values() for rs in bs.values() for r in rs]
    return {
        "scenarios": len(every_row),
        "failing": sum(1 for r in every_row if r["outcome"] == "failed"),
        "domains": domains,
    }


def as_summary(data: dict[str, Any]) -> str:
    """The counts alone, for a line in a build log."""
    out = [f"{data['scenarios']} scenarios over {len(data['domains'])} components, "
           f"{data['failing']} failing."]
    for domain in data["domains"]:
        gap = f", {len(domain['unexercised'])} calls unexercised" if domain["unexercised"] else ""
        out.append(
            f"  {domain['domain']}: {domain['scenarios']} scenarios, "
            f"{domain['failing']} failing{gap}"
        )
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=pathlib.Path, help="the JSONL files a run wrote")
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "summary"),
        default="markdown",
        help="markdown for a person to read, json for a tool, summary for the counts",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        help="write here instead of standard output",
    )
    args = parser.parse_args()
    missing = [p for p in args.logs if not p.exists()]
    if missing:
        print(f"no such log: {', '.join(str(p) for p in missing)}", file=sys.stderr)
        return 1

    rows = rows_of(args.logs)
    match args.format:
        case "json":
            text = json.dumps(as_data(rows), indent=2, ensure_ascii=False)
        case "summary":
            text = as_summary(as_data(rows))
        case _:
            text = render(rows)

    if args.output is None:
        print(text)
    else:
        args.output.write_text(text + "\n", encoding="utf8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
