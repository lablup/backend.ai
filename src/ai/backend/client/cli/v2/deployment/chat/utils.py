"""Persistence helpers for ``./bai deployment chat`` storage.

Two on-disk JSON files live side by side under ``~/.backend.ai/``:

- ``deployment_chat.json`` — auto-managed endpoint cache (resolved from
  the manager). Refetched on cache miss; never user-edited. Loaded via
  :meth:`DeploymentChatCache.load`.
- ``deployment_chat_config.json`` — user-managed API keys for the
  inference endpoints. Stored in plaintext, so the file is written with
  ``0600`` permissions. Loaded via :meth:`DeploymentChatConfig.load`.
"""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any

from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCache,
    DeploymentChatConfig,
)
from ai.backend.client.cli.v2.helpers import CONFIG_DIR
from ai.backend.common.json import load_json

CHAT_CACHE_FILE = CONFIG_DIR / "deployment_chat.json"
CHAT_CONFIG_FILE = CONFIG_DIR / "deployment_chat_config.json"


def save_chat_cache(cache: DeploymentChatCache) -> None:
    """Write the chat cache and enforce ``0600`` permissions."""
    CHAT_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHAT_CACHE_FILE.write_text(cache.model_dump_json(indent=2), encoding="utf-8")
    CHAT_CACHE_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)


def save_chat_config(config: DeploymentChatConfig) -> None:
    """Write the chat config and enforce ``0600`` permissions."""
    CHAT_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHAT_CONFIG_FILE.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    CHAT_CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)


def mask_token(token: str | None) -> str:
    """Render a token as ``sk-***...***xxxx`` for diagnostic display."""
    if token is None:
        return "<unset>"
    if len(token) <= 8:
        return "***"
    return f"{token[:3]}***...***{token[-4:]}"


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
