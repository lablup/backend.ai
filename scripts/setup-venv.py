#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Build the virtualenv holding the python-default resolve at the versions python.lock pins.

Run from the repository root: ``scripts/setup-venv.py [--venv <dir>]``.
Installs the requirements ``python.lock`` was generated from, constrained to the locked
versions, plus ``EXTRA_REQUIREMENTS``, which the lock does not hold.
Exits 1 when a package ends up at a version other than the one the lock pins.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

EXTRA_REQUIREMENTS = ["pytest-rerunfailures==16.7"]


def python_version() -> str:
    match = re.search(r"CPython==([\d.]+)", Path("pants.toml").read_text())
    if match is None:
        sys.exit("pants.toml: no CPython==<version> interpreter constraint")
    return match.group(1)


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def lock_pins() -> dict[str, str]:
    lock = tomllib.loads(Path("python.lock").read_text())
    return {
        normalize(package["name"]): package["version"]
        for package in lock["package"]
        if "registry" in package.get("source", {})
    }


def run(*command: str) -> None:
    subprocess.run(command, check=True)


def main() -> int:
    version = python_version()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--venv",
        type=Path,
        default=Path(f"dist/export/python/virtualenvs/python-default/{version}"),
    )
    venv: Path = parser.parse_args().venv
    python = venv / "bin" / "python"

    requirements = json.loads(Path("python.lock.metadata").read_text())[
        "generated_with_requirements"
    ]
    pins = lock_pins()
    with tempfile.TemporaryDirectory() as work:
        requirements_file = Path(work) / "requirements.txt"
        constraints_file = Path(work) / "constraints.txt"
        requirements_file.write_text("\n".join([*requirements, *EXTRA_REQUIREMENTS]) + "\n")
        constraints_file.write_text(
            "".join(f"{name}=={pin}\n" for name, pin in sorted(pins.items()))
        )
        run("uv", "venv", "--clear", "--python", version, str(venv))
        run(
            "uv", "pip", "install", "--python", str(python),
            "-r", str(requirements_file), "-c", str(constraints_file),
        )  # fmt: skip

    frozen = subprocess.run(
        ["uv", "pip", "freeze", "--python", str(python)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    mismatched = []
    for line in frozen.splitlines():
        name, sep, installed = line.partition("==")
        locked = pins.get(normalize(name))
        if sep and locked is not None and locked != installed:
            mismatched.append(f"{name}=={installed} (lock: {locked})")
    if mismatched:
        print("Installed at a version other than python.lock:", file=sys.stderr)
        print("\n".join(mismatched), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
