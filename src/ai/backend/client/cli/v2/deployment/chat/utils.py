"""Persistence helpers for ``./bai deployment chat`` storage.

Two on-disk JSON files live side by side under ``~/.backend.ai/``:

- ``deployment_chat.json`` — auto-managed endpoint cache (resolved from
  the manager). Refetched on cache miss; never user-edited.
- ``deployment_chat_config.json`` — user-managed API keys for the
  inference endpoints. Stored in plaintext, so the file is written with
  ``0600`` permissions.
"""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCache,
    DeploymentChatCacheEntry,
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
    deployments: dict[UUID, DeploymentChatCacheEntry] = {}
    deployments_raw = raw.get("deployments") or {}
    if isinstance(deployments_raw, dict):
        for key, value in deployments_raw.items():
            try:
                dep_id = UUID(str(key))
            except ValueError:
                continue
            if not isinstance(value, dict):
                continue
            try:
                deployments[dep_id] = DeploymentChatCacheEntry.model_validate(value)
            except ValidationError:
                continue
    return DeploymentChatCache(deployments=deployments)


def save_chat_cache(cache: DeploymentChatCache, path: Path = CHAT_CACHE_FILE) -> None:
    """Atomically write the chat cache."""
    _atomic_write(path, cache.model_dump_json(indent=2))


def load_chat_config(path: Path = CHAT_CONFIG_FILE) -> DeploymentChatConfig:
    """Load the chat config; return an empty config when the file is absent or unreadable."""
    raw = _read_json(path)
    if raw is None:
        return DeploymentChatConfig()
    tokens: dict[UUID, str] = {}
    tokens_raw = raw.get("tokens") or {}
    if isinstance(tokens_raw, dict):
        for key, value in tokens_raw.items():
            try:
                dep_id = UUID(str(key))
            except ValueError:
                continue
            if isinstance(value, str):
                tokens[dep_id] = value
    return DeploymentChatConfig(tokens=tokens)


def save_chat_config(config: DeploymentChatConfig, path: Path = CHAT_CONFIG_FILE) -> None:
    """Atomically write the chat config and enforce ``0600`` permissions."""
    _atomic_write(path, config.model_dump_json(indent=2))


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


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path_str = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        tmp_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        tmp_path.replace(path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
