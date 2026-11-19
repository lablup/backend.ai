#!/usr/bin/env python3
"""Sum the run time of each test file from junit reports.

    compute-test-durations.py --junit-dir <dir> --out <file>

<dir> holds one directory per report artifact, ``junit-<suite>-<n>/``, each with the
``junit-*.xml`` files of ``run-pytest-shard.py``. Writes ``<file>`` as
``{"<suite>": {"<path>": <seconds>}}``: the ``time`` of every testcase of a file, summed.
The test file of a testcase is the longest dotted prefix of its ``classname`` that is a
file under the current directory. Run it from the repository root.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import xml.etree.ElementTree as ET


def source_file(classname: str) -> str | None:
    parts = classname.split(".")
    for end in range(len(parts), 0, -1):
        candidate = "/".join(parts[:end]) + ".py"
        if pathlib.Path(candidate).is_file():
            return candidate
    return None


def compute(junit_dir: pathlib.Path) -> dict[str, dict[str, float]]:
    durations: dict[str, dict[str, float]] = {}
    for artifact in sorted(p for p in junit_dir.glob("junit-*") if p.is_dir()):
        suite = artifact.name.split("-")[1]
        record = durations.setdefault(suite, {})
        for report in sorted(artifact.rglob("junit-*.xml")):
            for case in ET.parse(report).getroot().iter("testcase"):
                file = source_file(case.get("classname", ""))
                if file is not None:
                    record[file] = record.get(file, 0.0) + float(case.get("time", 0))
    return {s: {f: round(t, 3) for f, t in sorted(r.items())} for s, r in durations.items()}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--junit-dir", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()
    durations = compute(args.junit_dir)
    args.out.write_text(json.dumps(durations, indent=1) + "\n")
    for suite, record in durations.items():
        sys.stdout.write(f"{suite}: {len(record)} files, {sum(record.values()):.0f}s\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
