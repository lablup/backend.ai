"""Filesystem helpers for ``./bai deployment chat`` storage.

Two on-disk JSON files live side by side under ``~/.backend.ai/``:

- ``deployment_chat.json`` — auto-managed endpoint cache (resolved from
  the manager). Holds no secrets, written with default umask. Persisted
  via :meth:`DeploymentChatCache.save`.
- ``deployment_chat_config.json`` — user-managed API keys for the
  inference endpoints. Stored in plaintext, so the file is created with
  ``0600`` permissions. Persisted via :meth:`DeploymentChatConfig.save`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai.backend.client.cli.v2.helpers import CONFIG_DIR
from ai.backend.common.json import load_json

CHAT_CACHE_FILE = CONFIG_DIR / "deployment_chat.json"
CHAT_CONFIG_FILE = CONFIG_DIR / "deployment_chat_config.json"


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
