"""Filesystem helpers for ``./bai deployment chat`` storage.

``cache.json``, ``config.json`` (tokens) and ``history.json`` under
``~/.backend.ai/deployment_chat/`` are plain JSON files readable only by their owner.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai.backend.client.cli.v2.helpers import CONFIG_DIR
from ai.backend.client.owner_only_files import ensure_owner_only_file
from ai.backend.common.json import load_json

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
    """Write ``text`` to the owner-only file ``path``, creating its parent directories."""
    ensure_owner_only_file(path)
    path.write_text(text, encoding="utf-8")
