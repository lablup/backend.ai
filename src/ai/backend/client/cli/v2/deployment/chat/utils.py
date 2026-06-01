"""Filesystem helpers for ``./bai deployment chat`` storage.

Three on-disk JSON files live under ``~/.backend.ai/deployment_chat/`` —
``cache.json`` for the auto-managed endpoint cache, ``config.json`` for
user-supplied tokens, and ``history.json`` for per-deployment chat
transcripts. The per-feature subdirectory matches the existing
``session/`` layout used by ``./bai login``.

All three files are written as plain JSON (no atomic-rename, no special
POSIX permissions) to stay aligned with the existing CLI credential-storage
convention in :mod:`ai.backend.client.cli.v2.config_cmd`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai.backend.client.cli.v2.helpers import CONFIG_DIR
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
    """Write ``text`` to ``path`` after ensuring the parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
