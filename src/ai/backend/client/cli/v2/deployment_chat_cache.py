"""Local cache for ``./bai deployment chat`` per-deployment endpoint metadata.

Stores the manager-resolved ``endpoint_url`` and the served model name
discovered from the inference endpoint. Auto-managed: refetched on cache
miss, never user-edited. The user-supplied API key lives in a separate
file managed by ``deployment_chat_config``.

Persisted as a JSON file at ``~/.backend.ai/deployment_chat.json``.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ai.backend.client.cli.v2.helpers import CONFIG_DIR

CHAT_CACHE_FILE = CONFIG_DIR / "deployment_chat.json"
CHAT_CACHE_SCHEMA_VERSION = 1


class DeploymentChatCacheEntry(BaseModel):
    """One deployment's auto-managed endpoint metadata."""

    model_config = ConfigDict(frozen=True)

    endpoint_url: str
    default_model: str | None = None
    last_synced_at: datetime


class DeploymentChatCache(BaseModel):
    """In-memory representation of the chat cache file."""

    schema_version: int = Field(default=CHAT_CACHE_SCHEMA_VERSION)
    deployments: dict[UUID, DeploymentChatCacheEntry] = Field(default_factory=dict)

    def get(self, deployment_id: UUID) -> DeploymentChatCacheEntry | None:
        return self.deployments.get(deployment_id)

    def upsert(self, deployment_id: UUID, entry: DeploymentChatCacheEntry) -> None:
        self.deployments[deployment_id] = entry

    def remove(self, deployment_id: UUID) -> bool:
        return self.deployments.pop(deployment_id, None) is not None


class IncompatibleChatCacheError(Exception):
    """Raised when the on-disk cache file uses a newer schema than this build."""


def load_chat_cache(path: Path = CHAT_CACHE_FILE) -> DeploymentChatCache:
    """Load the chat cache; return an empty cache when the file is absent or unreadable."""
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
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = cache.model_dump_json(indent=2)
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
