#!/usr/bin/env python3
"""Run towncrier against the version-specific changelog file.

``pyproject.toml`` pins ``[tool.towncrier] filename`` to the frozen archive
``CHANGELOG.md``. This script copies that section into a temporary config at the
repository root with ``filename`` rewritten to the per-version-branch changelog
(see ``changelog_files``), runs towncrier with it, and removes the temporary
config afterwards.

The temporary config must live at the repository root because towncrier resolves
``directory`` and ``template`` relative to the config file's own directory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from changelog_files import CHANGELOG_DIR, changelog_filename

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
PANTS_TOML_PATH = REPO_ROOT / "pants.toml"
TEMP_CONFIG_PATH = REPO_ROOT / ".towncrier.generated.toml"
INTERPRETER_RE = re.compile(r'CPython==([^"]+)')


class UnsupportedConfigError(Exception):
    """The ``[tool.towncrier]`` section has a shape this script cannot rewrite."""


def load_towncrier_config() -> dict[str, Any]:
    with PYPROJECT_PATH.open("rb") as f:
        pyproject = tomllib.load(f)
    try:
        return pyproject["tool"]["towncrier"]
    except KeyError:
        raise UnsupportedConfigError(f"No [tool.towncrier] section in {PYPROJECT_PATH}") from None


def format_value(value: Any) -> str:
    # TOML basic strings share JSON's escaping rules.
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(format_value(item) for item in value) + "]"
    raise UnsupportedConfigError(f"Cannot serialize {value!r} back to TOML")


def render_config(config: dict[str, Any]) -> str:
    """Serialize the ``[tool.towncrier]`` section back to TOML.

    Only the shape this project actually uses is supported: scalar (or list of
    scalar) values plus the ``[[tool.towncrier.type]]`` array of tables. Anything
    else is an error rather than a best-effort guess.
    """
    lines = ["[tool.towncrier]"]
    for key, value in config.items():
        if key == "type":
            continue
        lines.append(f"{key} = {format_value(value)}")
    for entry in config.get("type", []):
        if not isinstance(entry, dict):
            raise UnsupportedConfigError(f"Unexpected [[tool.towncrier.type]] entry: {entry!r}")
        lines.append("")
        lines.append("[[tool.towncrier.type]]")
        for key, value in entry.items():
            lines.append(f"{key} = {format_value(value)}")
    return "\n".join(lines) + "\n"


def has_fragments(config: dict[str, Any]) -> bool:
    """Tell whether ``changes/`` holds any file towncrier would consume.

    Mirrors towncrier's own basename parsing: a fragment name is dot-separated
    and carries a known type directory in any position but the first, which
    excludes ``README.md`` and ``template.md``.
    """
    type_names = {entry["directory"] for entry in config.get("type", [])}
    fragment_dir = REPO_ROOT / config["directory"]
    if not fragment_dir.is_dir():
        return False
    for path in fragment_dir.iterdir():
        if not path.is_file():
            continue
        if type_names.intersection(path.name.split(".")[1:]):
            return True
    return False


def towncrier_lockset() -> str:
    match = INTERPRETER_RE.search(PANTS_TOML_PATH.read_text())
    if match is None:
        raise UnsupportedConfigError(
            f"Could not read the target CPython interpreter version from {PANTS_TOML_PATH}"
        )
    return f"towncrier/{match.group(1)}"


def run_towncrier(version: str, config_path: Path) -> None:
    env = {**os.environ, "LOCKSET": towncrier_lockset()}
    # towncrier writes the newsfile but does not create its parent directory.
    (REPO_ROOT / CHANGELOG_DIR).mkdir(exist_ok=True)
    subprocess.run(
        [
            "./py",
            "-m",
            "towncrier",
            "build",
            "--yes",
            "--config",
            str(config_path),
            "--version",
            version,
        ],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "version",
        nargs="?",
        help="Release version being prepared (defaults to the VERSION file)",
    )
    args = parser.parse_args()
    version = args.version or (REPO_ROOT / "VERSION").read_text().strip()

    try:
        config = load_towncrier_config()
        if not has_fragments(config):
            print(
                f"No news fragments in {config['directory']}; skipping towncrier.",
                file=sys.stderr,
            )
            return 0
        config["filename"] = changelog_filename(version)
        TEMP_CONFIG_PATH.write_text(render_config(config))
    except (UnsupportedConfigError, ValueError) as e:
        print(f"::error ::{e}", file=sys.stderr)
        return 1

    print(
        f"Writing the {version} changelog block to {config['filename']} ...",
        file=sys.stderr,
    )
    try:
        run_towncrier(version, TEMP_CONFIG_PATH)
    except subprocess.CalledProcessError as e:
        print(f"::error ::towncrier failed with exit code {e.returncode}", file=sys.stderr)
        return e.returncode
    finally:
        TEMP_CONFIG_PATH.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
