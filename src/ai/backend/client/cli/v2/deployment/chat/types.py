"""Type definitions for ``./bai deployment chat`` storage."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError

CACHE_ENTRY_TTL = timedelta(hours=24)
"""Endpoint cache entries older than this are treated as a cache miss."""


class DeploymentChatCacheEntry(BaseModel):
    """One deployment's auto-managed endpoint metadata."""

    endpoint_url: str
    default_model: str | None = None
    last_synced_at: datetime

    def is_expired(self, *, now: datetime, ttl: timedelta = CACHE_ENTRY_TTL) -> bool:
        """Whether this entry is older than the cache TTL window."""
        return now - self.last_synced_at >= ttl


class DeploymentChatCache(BaseModel):
    """In-memory representation of the chat cache file."""

    deployments: dict[UUID, DeploymentChatCacheEntry] = Field(default_factory=dict)

    def get(self, deployment_id: UUID) -> DeploymentChatCacheEntry | None:
        return self.deployments.get(deployment_id)

    def set(self, deployment_id: UUID, entry: DeploymentChatCacheEntry) -> None:
        self.deployments[deployment_id] = entry

    def remove(self, deployment_id: UUID) -> bool:
        return self.deployments.pop(deployment_id, None) is not None

    @classmethod
    def load(cls) -> Self:
        """Load the chat cache; return an empty cache when the file is absent or unreadable."""
        from ai.backend.client.cli.v2.deployment.chat.utils import (
            CHAT_CACHE_FILE,
            read_json_file,
        )

        raw = read_json_file(CHAT_CACHE_FILE)
        if raw is None:
            return cls()
        try:
            return cls.model_validate(raw)
        except ValidationError:
            print(
                f"WARNING: {CHAT_CACHE_FILE} is in an invalid format and was ignored.",
                file=sys.stderr,
            )
            return cls()

    def save(self) -> None:
        """Persist the cache. Holds no secrets, default umask applies."""
        from ai.backend.client.cli.v2.deployment.chat.utils import CHAT_CACHE_FILE

        _write_text_file(CHAT_CACHE_FILE, self.model_dump_json(indent=2), mode=None)


class DeploymentChatConfig(BaseModel):
    """Per-deployment API key registry (user-managed)."""

    tokens: dict[UUID, str] = Field(default_factory=dict)

    def get_token(self, deployment_id: UUID) -> str | None:
        return self.tokens.get(deployment_id)

    def set_token(self, deployment_id: UUID, token: str) -> None:
        self.tokens[deployment_id] = token

    def clear_token(self, deployment_id: UUID) -> bool:
        return self.tokens.pop(deployment_id, None) is not None

    @classmethod
    def load(cls) -> Self:
        """Load the chat config; return an empty config when the file is absent or unreadable."""
        from ai.backend.client.cli.v2.deployment.chat.utils import (
            CHAT_CONFIG_FILE,
            read_json_file,
        )

        raw = read_json_file(CHAT_CONFIG_FILE)
        if raw is None:
            return cls()
        try:
            return cls.model_validate(raw)
        except ValidationError:
            print(
                f"WARNING: {CHAT_CONFIG_FILE} is in an invalid format and was ignored. "
                "Re-register tokens with `./bai deployment chat-config set`.",
                file=sys.stderr,
            )
            return cls()

    def save(self) -> None:
        """Persist the config with ``0600`` permissions because it stores plaintext API keys."""
        from ai.backend.client.cli.v2.deployment.chat.utils import CHAT_CONFIG_FILE

        _write_text_file(CHAT_CONFIG_FILE, self.model_dump_json(indent=2), mode=0o600)


def _write_text_file(path: Path, text: str, *, mode: int | None) -> None:
    """Write ``text`` to ``path`` via a tmp-and-rename so partial writes can't
    corrupt the destination. When ``mode`` is given, the temp file is created
    with that POSIX permission so the final file never exists with weaker
    permissions, even briefly.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    open_mode = mode if mode is not None else 0o666
    fd = os.open(tmp, flags, open_mode)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
