#!/usr/bin/env python3
"""Run one shard of a test list with pytest, without Pants.

    run-pytest-shard.py --list <file> --shard k/N --mode per-file|batched \\
        --junit-dir <dir> --python <python> [--workers <n>] [-- <pytest arguments>]

<file> lists test files, one path per line. The shard holds the files with
``crc32(path) % N == k``, the split ``plan-ci-targets.py`` plans. ``--workers`` processes
(default ``os.cpu_count()``) run side by side, each with its own
``BACKEND_TEST_EXEC_SLOT``, the container slot of ``tests/README.md``:

=============== =====================================================================
``per-file``    one pytest process per file
``batched``     the files in ``workers`` * 2 batches, one pytest process per batch
=============== =====================================================================

The pytest options are those of the ``[test]`` section of ``pants.toml``: a 180 second
timeout per test and one rerun of a failed test. Each process writes
``<junit-dir>/junit-<n>.xml``. Exit code 1 when a process exits with a code other than
0 and 5 (no tests collected). The totals, the sum of the process times and the failed
tests go to the file named by ``--summary`` (default: print them) and each failed test is a ``::error`` annotation.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import queue
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
import zlib

TIMEOUT = 180
RERUNS = 1
OK_CODES = (0, 5)


def out(text: str) -> None:
    sys.stdout.write(f"{text}\n")
    sys.stdout.flush()


def parse_shard(value: str) -> tuple[int, int]:
    index, _, count = value.partition("/")
    return int(index), int(count)


def select(listing: pathlib.Path, index: int, count: int) -> list[str]:
    paths = [p.strip() for p in listing.read_text().splitlines() if p.strip()]
    return [p for p in paths if zlib.crc32(p.encode()) % count == index]


def split_batches(files: list[str], mode: str, workers: int) -> list[list[str]]:
    if mode == "per-file":
        return [[f] for f in files]
    count = min(len(files), workers * 2)
    return [files[i::count] for i in range(count)]


def run_all(
    batches: list[list[str]],
    workers: int,
    command: list[str],
    junit_dir: pathlib.Path,
    env: dict[str, str],
) -> list[tuple[int, float]]:
    pending: queue.Queue[tuple[int, list[str]]] = queue.Queue()
    for n, batch in enumerate(batches):
        pending.put((n, batch))
    results: list[tuple[int, float]] = []
    lock = threading.Lock()

    def work(slot: int) -> None:
        while True:
            try:
                n, batch = pending.get_nowait()
            except queue.Empty:
                return
            started = time.monotonic()
            result = subprocess.run(
                [*command, f"--junitxml={junit_dir}/junit-{n}.xml", *batch],
                env={**env, "BACKEND_TEST_EXEC_SLOT": str(slot)},
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            elapsed = time.monotonic() - started
            title = batch[0] if len(batch) == 1 else f"{len(batch)} files from {batch[0]}"
            with lock:
                results.append((result.returncode, elapsed))
                out(f"::group::{title} (slot {slot}, {elapsed:.1f}s, exit {result.returncode})")
                out(result.stdout)
                out("::endgroup::")

    threads = [threading.Thread(target=work, args=(slot,)) for slot in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results


def source_file(classname: str) -> str:
    """The test file of a junit ``classname``: the longest dotted prefix that is a file."""
    parts = classname.split(".")
    for end in range(len(parts), 0, -1):
        candidate = "/".join(parts[:end]) + ".py"
        if pathlib.Path(candidate).is_file():
            return candidate
    return classname.replace(".", "/") + ".py"


def summarize(junit_dir: pathlib.Path, times: list[float]) -> str:
    total = dict.fromkeys(("tests", "failures", "errors", "skipped"), 0)
    failed: list[tuple[str, str]] = []
    for path in sorted(junit_dir.glob("junit-*.xml")):
        root = ET.parse(path).getroot()
        for suite in [root] if root.tag == "testsuite" else list(root):
            for key in total:
                total[key] += int(suite.get(key, 0))
        for case in root.iter("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                classname = case.get("classname", "")
                file = source_file(classname)
                failed.append((file, f"{classname}::{case.get('name')}"))
    lines = [
        f"### Tests: {total['tests']} run, {total['failures']} failed, "
        f"{total['errors']} errors, {total['skipped']} skipped",
        "",
        f"Process time: {sum(times):.0f}s in total over {len(times)} processes, "
        f"longest {max(times, default=0.0):.0f}s",
        "",
    ]
    for file, name in sorted(failed):
        lines.append(f"- FAILED `{name}`")
        out(f"::error file={file}::{name}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--list", required=True, type=pathlib.Path)
    parser.add_argument("--shard", required=True)
    parser.add_argument("--mode", required=True, choices=("per-file", "batched"))
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--junit-dir", required=True, type=pathlib.Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--summary", type=pathlib.Path)
    parser.add_argument("pytest_args", nargs="*")
    args = parser.parse_args()

    index, count = parse_shard(args.shard)
    files = select(args.list, index, count)
    if not files:
        out("No tests in this shard")
        return 0
    args.junit_dir.mkdir(parents=True, exist_ok=True)
    root = pathlib.Path.cwd()
    env = {
        **os.environ,
        "PYTHONPATH": f"{root}/src:{root}/tests/scenario:{root}",
        "BACKEND_BUILD_ROOT": str(root),
    }
    command = [
        args.python,
        "-m",
        "pytest",
        "--import-mode=importlib",
        f"--timeout={TIMEOUT}",
        f"--reruns={RERUNS}",
        "-vv",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "-o",
        "junit_family=xunit2",
        *args.pytest_args,
    ]
    batches = split_batches(files, args.mode, max(1, args.workers))
    out(f"shard {args.shard}: {len(files)} files, {len(batches)} processes")
    results = run_all(batches, max(1, args.workers), command, args.junit_dir, env)
    summary = summarize(args.junit_dir, [elapsed for _, elapsed in results])
    if args.summary is not None:
        with args.summary.open("a") as f:
            f.write(summary)
    else:
        out(summary)
    return 1 if any(code not in OK_CODES for code, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main())
