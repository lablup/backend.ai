"""Local cache for ``./bai deployment chat`` per-deployment settings.

Stores ``endpoint_url`` (resolved from the manager) and the inference API
key the user registered for each deployment so that follow-up ``chat``
invocations do not need to re-query the manager nor re-prompt for the key.

Persisted as a single JSON file at ``~/.backend.ai/deployment_chat.json``
with ``0600`` file permissions because the API key is stored in plaintext.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from ai.backend.client.cli.v2.helpers import CONFIG_DIR

CHAT_CACHE_FILE = CONFIG_DIR / "deployment_chat.json"
CHAT_CACHE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class DeploymentChatCacheEntry:
    """One deployment's chat configuration."""

    endpoint_url: str
    api_key: str | None
    default_model: str | None
    last_synced_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint_url": self.endpoint_url,
            "api_key": self.api_key,
            "default_model": self.default_model,
            "last_synced_at": self.last_synced_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeploymentChatCacheEntry:
        synced_raw = data.get("last_synced_at")
        if isinstance(synced_raw, str):
            synced = datetime.fromisoformat(synced_raw)
        else:
            synced = datetime.now(UTC)
        return cls(
            endpoint_url=str(data["endpoint_url"]),
            api_key=(str(data["api_key"]) if data.get("api_key") is not None else None),
            default_model=(
                str(data["default_model"]) if data.get("default_model") is not None else None
            ),
            last_synced_at=synced,
        )


@dataclass
class DeploymentChatCache:
    """In-memory representation of the chat cache file."""

    entries: dict[UUID, DeploymentChatCacheEntry] = field(default_factory=dict)

    def get(self, deployment_id: UUID) -> DeploymentChatCacheEntry | None:
        return self.entries.get(deployment_id)

    def upsert(self, deployment_id: UUID, entry: DeploymentChatCacheEntry) -> None:
        self.entries[deployment_id] = entry

    def remove(self, deployment_id: UUID) -> bool:
        return self.entries.pop(deployment_id, None) is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": CHAT_CACHE_SCHEMA_VERSION,
            "deployments": {str(dep_id): entry.to_dict() for dep_id, entry in self.entries.items()},
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
    deployments_raw = raw.get("deployments") or {}
    entries: dict[UUID, DeploymentChatCacheEntry] = {}
    if isinstance(deployments_raw, dict):
        for key, value in deployments_raw.items():
            try:
                dep_id = UUID(str(key))
            except ValueError:
                continue
            if not isinstance(value, dict):
                continue
            try:
                entries[dep_id] = DeploymentChatCacheEntry.from_dict(value)
            except (KeyError, ValueError, TypeError):
                continue
    return DeploymentChatCache(entries=entries)


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
