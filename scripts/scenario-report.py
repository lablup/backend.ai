#!/usr/bin/env python3
"""Turn the records a scenario run wrote into a report grouped by component.

Each scenario appends one JSON record to the file named by ``BACKEND_SCENARIO_LOG``
while the tests run. Pants gives every test file its own process and every shard its own
machine, so the records arrive interleaved and possibly in several files; this merges
them and prints what each component now covers.

    BACKEND_SCENARIO_LOG=dist/scenarios.jsonl pants test tests/scenario::
    python scripts/scenario-report.py dist/scenarios.jsonl -o dist/scenarios.md
    python scripts/scenario-report.py dist/scenarios.jsonl --format json

The report itself lives in ``ai.backend.testutils.scenario_report``, which the run also
uses to write the records. This file only reads the arguments and the files.
"""

from __future__ import annotations

import argparse
import pathlib
import sys


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
    parser.add_argument(
        "--verify",
        type=pathlib.Path,
        metavar="DIR",
        help="check DIR/<component>/report.md against this run; write nothing",
    )
    parser.add_argument(
        "--split",
        type=pathlib.Path,
        metavar="DIR",
        help="write DIR/<component>/report.md for every component this run covered",
    )
    args = parser.parse_args()
    missing = [p for p in args.logs if not p.exists()]
    if missing:
        print(f"no such log: {', '.join(str(p) for p in missing)}", file=sys.stderr)
        return 1

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
    from ai.backend.testutils.scenario_report import (
        JsonFormat,
        MarkdownFormat,
        Report,
        ReportFormat,
        SummaryFormat,
        records_of,
    )

    chosen: ReportFormat
    match args.format:
        case "json":
            chosen = JsonFormat()
        case "summary":
            chosen = SummaryFormat()
        case _:
            chosen = MarkdownFormat()

    lines = [
        line for path in args.logs for line in path.read_text(encoding="utf8").splitlines()
    ]
    report = Report.of(records_of(lines))
    if args.verify is not None:
        drifted = 0
        for component in report.components:
            written = args.verify / component.component / f"report.{chosen.suffix()}"
            wanted = chosen.render_one(component) + "\n"
            if not written.exists():
                print(f"{written}: not written yet", file=sys.stderr)
                drifted += 1
            elif written.read_text(encoding="utf8") != wanted:
                print(f"{written}: no longer matches the run", file=sys.stderr)
                drifted += 1
        if drifted:
            print(
                f"{drifted} report(s) behind the run. Read what changed, then bring "
                "them level with --split.",
                file=sys.stderr,
            )
            return 1
        print(f"{len(report.components)} report(s) level with the run")
        return 0

    if args.split is not None:
        for component in report.components:
            written = args.split / component.component / f"report.{chosen.suffix()}"
            written.parent.mkdir(parents=True, exist_ok=True)
            written.write_text(chosen.render_one(component) + "\n", encoding="utf8")
            print(written)
        return 0

    text = chosen.render(report)
    if args.output is None:
        print(text)
    else:
        args.output.write_text(text + "\n", encoding="utf8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
