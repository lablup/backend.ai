"""Filesystem helpers for ``./bai deployment chat`` storage.

Three on-disk JSON files live under ``~/.backend.ai/deployment_chat/`` —
``cache.json`` for the auto-managed endpoint cache, ``config.json`` for
user-supplied tokens, and ``history.json`` for per-deployment chat
transcripts. The per-feature subdirectory matches the existing
``session/`` layout used by ``./bai login``. ``config.json`` is readable
only by its owner.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ai.backend.client.cli.v2.helpers import CONFIG_DIR
from ai.backend.common.json import load_json

_OWNER_ONLY_FILE_MODE = 0o600

CHAT_DIR = CONFIG_DIR / "deployment_chat"
CHAT_CACHE_FILE = CHAT_DIR / "cache.json"
CHAT_CONFIG_FILE = CHAT_DIR / "config.json"
CHAT_HISTORY_FILE = CHAT_DIR / "history.json"


def read_json_file(path: Path) -> dict[str, Any] | None:
    """Read a JSON file as a dict, returning None on missing or unparseable input."""
    if not path.exists():
        return None
    try:
        with path.open("rb") as f:
            raw = load_json(f.read())
    except (OSError, ValueError):
        return None
    return raw if isinstance(raw, dict) else None


def write_json_file(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` after ensuring the parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_owner_only_json_file(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` readable only by its owner, creating the parent directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(
        path,
        "w",
        encoding="utf-8",
        opener=lambda opened_path, flags: os.open(opened_path, flags, _OWNER_ONLY_FILE_MODE),
    ) as owner_only_file:
        os.fchmod(owner_only_file.fileno(), _OWNER_ONLY_FILE_MODE)
        owner_only_file.write(text)
