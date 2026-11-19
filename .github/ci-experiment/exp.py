#!/usr/bin/env python3
"""Helpers of the ci-experiment workflow.

exp.py time <log> <label> -- <command...>   run a command, append its seconds to <log>
exp.py note <log> <label> <value>           append a value to <log>
exp.py summary <log> <title>                print <log> as a Markdown table
exp.py pins <python.lock>                   print `name==version` of every locked package
exp.py requirements <python.lock.metadata>  print the requirements the lock was made from
exp.py shard <list> <index> <count>         print the paths with crc32(path) % count == index
exp.py addresses <list>                     print the files of Pants addresses
exp.py compare <ours> <pants>               print the paths only one of the lists holds
exp.py batches <list> <workers> <size> <junit-prefix> -- <pytest...>
                                            run the list in batches of <size> files on
                                            <workers> processes, each its own
                                            BACKEND_TEST_EXEC_SLOT
exp.py fixtures <log>                       print the container fixture setup totals
exp.py existing <list>                      print the paths of the list that exist
exp.py forced <changed> <suite>             print the changed files that make testmon run
                                            the whole list of <suite>
exp.py selected <collect-output> <out>      write the files of `pytest --co -q` test ids to
                                            <out>, print the file and test counts
"""

from __future__ import annotations

import json
import os
import pathlib
import queue
import subprocess
import sys
import threading
import time
import tomllib
import zlib


def out(text: str) -> None:
    sys.stdout.write(f"{text}\n")


def cmd_time(log: str, label: str, command: list[str]) -> int:
    start = time.monotonic()
    code = subprocess.call(command)
    elapsed = time.monotonic() - start
    with pathlib.Path(log).open("a") as f:
        f.write(f"{label}\t{elapsed:.1f}s\texit {code}\n")
    return code


def cmd_note(log: str, label: str, value: str) -> int:
    with pathlib.Path(log).open("a") as f:
        f.write(f"{label}\t{value}\t\n")
    return 0


def cmd_summary(log: str, title: str) -> int:
    path = pathlib.Path(log)
    lines = path.read_text().splitlines() if path.exists() else []
    out(f"### {title}\n\n| Step | Value | Result |\n|---|---|---|")
    for line in lines:
        label, value, result = (line.split("\t") + ["", ""])[:3]
        out(f"| {label} | {value} | {result} |")
    return 0


def cmd_pins(lock: str) -> int:
    data = tomllib.loads(pathlib.Path(lock).read_text())
    for package in data["package"]:
        if "registry" in package.get("source", {}):
            out(f"{package['name']}=={package['version']}")
    return 0


def cmd_requirements(metadata: str) -> int:
    for requirement in json.loads(pathlib.Path(metadata).read_text())[
        "generated_with_requirements"
    ]:
        out(requirement)
    return 0


def read_list(path: str) -> list[str]:
    return [line.strip() for line in pathlib.Path(path).read_text().splitlines() if line.strip()]


def cmd_shard(listing: str, index: str, count: str) -> int:
    for path in read_list(listing):
        if zlib.crc32(path.encode()) % int(count) == int(index):
            out(path)
    return 0


def cmd_addresses(listing: str) -> int:
    files = set()
    for address in read_list(listing):
        path = address.partition(":")[0]
        if path.endswith((".py", ".pyi")):
            files.add(path)
    for path in sorted(files):
        out(path)
    return 0


def cmd_compare(ours: str, pants: str) -> int:
    a, b = set(read_list(ours)), set(read_list(pants))
    out(f"only-ours={len(a - b)} only-pants={len(b - a)} both={len(a & b)}")
    for path in sorted(a - b):
        out(f"+ {path}")
    for path in sorted(b - a):
        out(f"- {path}")
    return 0


def cmd_batches(listing: str, workers: str, size: str, junit: str, command: list[str]) -> int:
    files = read_list(listing)
    step = int(size)
    batches = queue.Queue[tuple[int, list[str]]]()
    for k, start in enumerate(range(0, len(files), step)):
        batches.put((k, files[start : start + step]))
    codes: list[int] = []
    lock = threading.Lock()

    def work(slot: int) -> None:
        env = {**os.environ, "BACKEND_TEST_EXEC_SLOT": str(slot)}
        while True:
            try:
                k, batch = batches.get_nowait()
            except queue.Empty:
                return
            start = time.monotonic()
            result = subprocess.run(
                [*command, f"--junitxml={junit}-{k}.xml", *batch],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            elapsed = time.monotonic() - start
            with lock:
                codes.append(result.returncode)
                out(
                    f"::group::batch {k} slot {slot} {len(batch)} files {elapsed:.1f}s exit {result.returncode}"
                )
                out(result.stdout)
                out("::endgroup::")
                out(f"batch {k}: {len(batch)} files, {elapsed:.1f}s, exit {result.returncode}")

    threads = [threading.Thread(target=work, args=(slot,)) for slot in range(int(workers))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return 1 if any(c not in (0, 5) for c in codes) else 0


def cmd_fixtures(log: str) -> int:
    totals: dict[str, list[float]] = {}
    path = pathlib.Path(log)
    for line in path.read_text().splitlines() if path.exists() else []:
        name, seconds = line.split("\t")
        totals.setdefault(name, []).append(float(seconds))
    every = [s for v in totals.values() for s in v]
    out(f"containers\t{sum(every):.1f}s in {len(every)} setups, max {max(every, default=0):.1f}s\t")
    for name, values in sorted(totals.items()):
        out(f"{name}\t{sum(values):.1f}s in {len(values)} setups, max {max(values):.1f}s\t")
    return 0


def cmd_existing(listing: str) -> int:
    for path in read_list(listing):
        if pathlib.Path(path).is_file():
            out(path)
    return 0


def cmd_forced(changed: str, suite: str) -> int:
    # testmon sees the code a test runs, not what a conftest does at import time or what
    # a BUILD, pyproject.toml or python.lock decides.
    scope = pathlib.PurePosixPath("tests", suite)
    for path in read_list(changed):
        p = pathlib.PurePosixPath(path)
        in_scope = p.parts[0] != "tests" or p.parent in scope.parents or scope in p.parents
        if path in ("pyproject.toml", "python.lock", "python.lock.metadata") or (
            p.name in ("conftest.py", "BUILD") and in_scope
        ):
            out(path)
    return 0


def cmd_selected(collected: str, output: str) -> int:
    tests = [
        line.strip() for line in pathlib.Path(collected).read_text().splitlines() if "::" in line
    ]
    files = sorted({test.split("::", 1)[0] for test in tests})
    pathlib.Path(output).write_text("".join(f"{path}\n" for path in files))
    out(f"{len(files)} files, {len(tests)} tests")
    return 0


def main(argv: list[str]) -> int:
    match argv:
        case ["time", log, label, "--", *command]:
            return cmd_time(log, label, command)
        case ["note", log, label, value]:
            return cmd_note(log, label, value)
        case ["summary", log, title]:
            return cmd_summary(log, title)
        case ["pins", lock]:
            return cmd_pins(lock)
        case ["requirements", metadata]:
            return cmd_requirements(metadata)
        case ["shard", listing, index, count]:
            return cmd_shard(listing, index, count)
        case ["addresses", listing]:
            return cmd_addresses(listing)
        case ["compare", ours, pants]:
            return cmd_compare(ours, pants)
        case ["fixtures", log]:
            return cmd_fixtures(log)
        case ["existing", listing]:
            return cmd_existing(listing)
        case ["forced", changed, suite]:
            return cmd_forced(changed, suite)
        case ["selected", collected, output]:
            return cmd_selected(collected, output)
        case ["batches", listing, workers, size, junit, "--", *command]:
            return cmd_batches(listing, workers, size, junit, command)
    sys.stderr.write(__doc__ or "")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
