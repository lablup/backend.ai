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
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
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
    sys.stderr.write(__doc__ or "")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
