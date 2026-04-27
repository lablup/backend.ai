"""Local cache for ``./bai deployment chat`` per-deployment settings.

Persists the manager-resolved ``endpoint_url`` and the served model name
discovered from the inference endpoint, plus a separate map of API keys
the user registered through ``./bai deployment chat-config set``. The
endpoint entry is auto-managed (refetched when missing); the token is
user-supplied and never auto-discovered.

Stored as a single JSON file at ``~/.backend.ai/deployment_chat.json``
with ``0600`` permissions because the API keys are kept in plaintext.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, ValidationError

from ai.backend.client.cli.v2.helpers import CONFIG_DIR

CHAT_CACHE_FILE = CONFIG_DIR / "deployment_chat.json"
CHAT_CACHE_SCHEMA_VERSION = 1


class DeploymentChatCacheEntry(BaseModel):
    """One deployment's auto-managed endpoint metadata."""

    model_config = ConfigDict(frozen=True)

    endpoint_url: str
    default_model: str | None = None
    last_synced_at: datetime


@dataclass
class DeploymentChatCache:
    """In-memory representation of the chat cache file.

    ``entries`` is the auto-managed endpoint cache; ``tokens`` is the
    user-managed API-key store. They are kept in the same file under
    distinct top-level keys.
    """

    entries: dict[UUID, DeploymentChatCacheEntry] = field(default_factory=dict)
    tokens: dict[UUID, str] = field(default_factory=dict)

    def get(self, deployment_id: UUID) -> DeploymentChatCacheEntry | None:
        return self.entries.get(deployment_id)

    def upsert(self, deployment_id: UUID, entry: DeploymentChatCacheEntry) -> None:
        self.entries[deployment_id] = entry

    def remove(self, deployment_id: UUID) -> bool:
        had_entry = self.entries.pop(deployment_id, None) is not None
        had_token = self.tokens.pop(deployment_id, None) is not None
        return had_entry or had_token

    def get_token(self, deployment_id: UUID) -> str | None:
        return self.tokens.get(deployment_id)

    def set_token(self, deployment_id: UUID, token: str) -> None:
        self.tokens[deployment_id] = token

    def clear_token(self, deployment_id: UUID) -> bool:
        return self.tokens.pop(deployment_id, None) is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": CHAT_CACHE_SCHEMA_VERSION,
            "deployments": {
                str(dep_id): entry.model_dump(mode="json") for dep_id, entry in self.entries.items()
            },
            "tokens": {str(dep_id): token for dep_id, token in self.tokens.items()},
        }


class IncompatibleChatCacheError(Exception):
    """Raised when the on-disk cache file uses a newer schema than this build."""


def load_chat_cache(path: Path = CHAT_CACHE_FILE) -> DeploymentChatCache:
    """Load the chat cache; return an empty cache when the file is absent or unreadable.

    A corrupted JSON file or unreadable file is treated as an empty cache —
    individual malformed entries are skipped rather than aborting the whole
    load. A schema version newer than this build raises
    :class:`IncompatibleChatCacheError` so the caller can warn the user.
    """
    if not path.exists():
        return DeploymentChatCache()
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError):
        return DeploymentChatCache()
    if not isinstance(raw, dict):
        return DeploymentChatCache()
    schema = raw.get("schema_version")
    if schema is not None and isinstance(schema, int) and schema > CHAT_CACHE_SCHEMA_VERSION:
        raise IncompatibleChatCacheError(
            f"deployment_chat.json schema version {schema} is newer than supported "
            f"{CHAT_CACHE_SCHEMA_VERSION}; please upgrade the client."
        )
    entries: dict[UUID, DeploymentChatCacheEntry] = {}
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
                entries[dep_id] = DeploymentChatCacheEntry.model_validate(value)
            except ValidationError:
                continue
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
    return DeploymentChatCache(entries=entries, tokens=tokens)


def save_chat_cache(cache: DeploymentChatCache, path: Path = CHAT_CACHE_FILE) -> None:
    """Atomically write the chat cache and enforce ``0600`` permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(cache.to_dict(), indent=2, ensure_ascii=False)
    fd, tmp_path_str = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        tmp_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        tmp_path.replace(path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def mask_token(token: str | None) -> str:
    """Render a token as ``sk-***...***xxxx`` for diagnostic display."""
    if token is None:
        return "<unset>"
    if len(token) <= 8:
        return "***"
    return f"{token[:3]}***...***{token[-4:]}"
