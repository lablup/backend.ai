"""Type definitions for ``./bai deployment chat`` storage."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
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

    def is_fresh(self, *, now: datetime, ttl: timedelta = CACHE_ENTRY_TTL) -> bool:
        """Whether this entry is within the cache TTL window."""
        return now - self.last_synced_at < ttl


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
