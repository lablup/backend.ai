"""Module, not a command: news fragment names and the towncrier settings they depend on."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

# `<YYYYMMDD>-<HHMMSS>-<6 lowercase letters or digits>.<type>.md`, renamed at release time.
UNNUMBERED_RE = re.compile(r"^(?P<stamp>\d{8}-\d{6}-[a-z0-9]{6})\.(?P<type>[a-z]+)\.md$")
NUMBERED_RE = re.compile(r"^\d+\.")


def load_fragment_settings(repo_root: Path) -> tuple[Path, list[str]]:
    """Return the fragment directory and the fragment types from `pyproject.toml`."""
    with (repo_root / "pyproject.toml").open("rb") as f:
        config = tomllib.load(f)["tool"]["towncrier"]
    return repo_root / config["directory"], [entry["directory"] for entry in config["type"]]


def is_fragment(name: str, types: list[str]) -> bool:
    """Tell whether towncrier reads `name` as a fragment: a known type after the first dot."""
    return bool(set(types).intersection(name.split(".")[1:]))
