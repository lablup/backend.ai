"""Local cache for ``./bai deployment chat`` per-deployment settings.

Stores ``endpoint_url`` and the vLLM API key the user registered for each
deployment so that follow-up ``chat`` invocations do not need to re-query
the manager nor re-prompt for the API key.

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
    vllm_api_key: str | None
    default_model: str | None
    last_synced_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint_url": self.endpoint_url,
            "vllm_api_key": self.vllm_api_key,
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
            vllm_api_key=(
                str(data["vllm_api_key"]) if data.get("vllm_api_key") is not None else None
            ),
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
    """Load the chat cache; return an empty cache when the file is absent."""
    if not path.exists():
        return DeploymentChatCache()
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
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
            if isinstance(value, dict):
                entries[dep_id] = DeploymentChatCacheEntry.from_dict(value)
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
