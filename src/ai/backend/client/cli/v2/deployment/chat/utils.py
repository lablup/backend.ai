"""Persistence helpers for ``./bai deployment chat`` storage.

Two on-disk JSON files live side by side under ``~/.backend.ai/``:

- ``deployment_chat.json`` — auto-managed endpoint cache (resolved from
  the manager). Refetched on cache miss; never user-edited.
- ``deployment_chat_config.json`` — user-managed API keys for the
  inference endpoints. Stored in plaintext, so the file is written with
  ``0600`` permissions.
"""

from __future__ import annotations

import stat
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCache,
    DeploymentChatConfig,
)
from ai.backend.client.cli.v2.helpers import CONFIG_DIR
from ai.backend.common.json import load_json

CHAT_CACHE_FILE = CONFIG_DIR / "deployment_chat.json"
CHAT_CONFIG_FILE = CONFIG_DIR / "deployment_chat_config.json"


def load_chat_cache(path: Path = CHAT_CACHE_FILE) -> DeploymentChatCache:
    """Load the chat cache; return an empty cache when the file is absent or unreadable."""
    raw = _read_json(path)
    if raw is None:
        return DeploymentChatCache()
    try:
        return DeploymentChatCache.model_validate(raw)
    except ValidationError:
        print(
            f"WARNING: {path} is in an invalid format and was ignored.",
            file=sys.stderr,
        )
        return DeploymentChatCache()


def save_chat_cache(cache: DeploymentChatCache, path: Path = CHAT_CACHE_FILE) -> None:
    """Write the chat cache and enforce ``0600`` permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cache.model_dump_json(indent=2), encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def load_chat_config(path: Path = CHAT_CONFIG_FILE) -> DeploymentChatConfig:
    """Load the chat config; return an empty config when the file is absent or unreadable."""
    raw = _read_json(path)
    if raw is None:
        return DeploymentChatConfig()
    try:
        return DeploymentChatConfig.model_validate(raw)
    except ValidationError:
        print(
            f"WARNING: {path} is in an invalid format and was ignored. "
            "Re-register tokens with `./bai deployment chat-config set`.",
            file=sys.stderr,
        )
        return DeploymentChatConfig()


def save_chat_config(config: DeploymentChatConfig, path: Path = CHAT_CONFIG_FILE) -> None:
    """Write the chat config and enforce ``0600`` permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def mask_token(token: str | None) -> str:
    """Render a token as ``sk-***...***xxxx`` for diagnostic display."""
    if token is None:
        return "<unset>"
    if len(token) <= 8:
        return "***"
    return f"{token[:3]}***...***{token[-4:]}"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with path.open("rb") as f:
            raw = load_json(f.read())
    except (OSError, ValueError):
        return None
    return raw if isinstance(raw, dict) else None
