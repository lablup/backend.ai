"""Type definitions for ``./bai deployment chat`` storage."""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Annotated, Self

from pydantic import BaseModel, Field, ValidationError

from ai.backend.client.cli.v2.deployment.chat.utils import (
    CHAT_CACHE_FILE,
    CHAT_CONFIG_FILE,
    read_json_file,
    write_json_file,
)
from ai.backend.common.identifier.deployment import DeploymentID

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

    deployments: dict[DeploymentID, DeploymentChatCacheEntry] = Field(default_factory=dict)

    def get(self, deployment_id: DeploymentID) -> DeploymentChatCacheEntry | None:
        return self.deployments.get(deployment_id)

    def set(self, deployment_id: DeploymentID, entry: DeploymentChatCacheEntry) -> None:
        self.deployments[deployment_id] = entry

    def pop(self, deployment_id: DeploymentID) -> bool:
        return self.deployments.pop(deployment_id, None) is not None

    @classmethod
    def load(cls) -> Self:
        """Load the chat cache; return an empty cache when the file is absent or unreadable."""
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
        """Persist the cache as a plain JSON file (matches existing CLI credential
        storage convention; see ``client/cli/v2/config_cmd.py``).
        """
        write_json_file(CHAT_CACHE_FILE, self.model_dump_json(indent=2))


class DeploymentChatConfigEntry(BaseModel):
    """One deployment's user-managed state.

    ``model`` holds the user's explicit ``--model`` choice for a deployment;
    it takes precedence over :attr:`DeploymentChatCacheEntry.default_model`
    (which is the value the CLI auto-derived from ``GET /v1/models``).
    """

    token: str | None = None
    model: str | None = None

    def is_empty(self) -> bool:
        return self.token is None and self.model is None


class DeploymentChatConfig(BaseModel):
    """Per-deployment user-managed registry (tokens + chosen model name)."""

    deployments: defaultdict[
        DeploymentID,
        Annotated[DeploymentChatConfigEntry, Field(default_factory=DeploymentChatConfigEntry)],
    ] = Field(default_factory=lambda: defaultdict(DeploymentChatConfigEntry))

    def get(self, deployment_id: DeploymentID) -> DeploymentChatConfigEntry | None:
        return self.deployments.get(deployment_id)

    def get_token(self, deployment_id: DeploymentID) -> str | None:
        entry = self.deployments.get(deployment_id)
        return entry.token if entry is not None else None

    def get_model(self, deployment_id: DeploymentID) -> str | None:
        entry = self.deployments.get(deployment_id)
        return entry.model if entry is not None else None

    def set_token(self, deployment_id: DeploymentID, token: str) -> None:
        self.deployments[deployment_id].token = token

    def set_model(self, deployment_id: DeploymentID, model: str) -> None:
        self.deployments[deployment_id].model = model

    def pop_token(self, deployment_id: DeploymentID) -> bool:
        entry = self.deployments.get(deployment_id)
        if entry is None or entry.token is None:
            return False
        entry.token = None
        if entry.is_empty():
            del self.deployments[deployment_id]
        return True

    def pop_model(self, deployment_id: DeploymentID) -> bool:
        entry = self.deployments.get(deployment_id)
        if entry is None or entry.model is None:
            return False
        entry.model = None
        if entry.is_empty():
            del self.deployments[deployment_id]
        return True

    def pop(self, deployment_id: DeploymentID) -> bool:
        return self.deployments.pop(deployment_id, None) is not None

    @classmethod
    def load(cls) -> Self:
        """Load the chat config; return an empty config when the file is absent or unreadable."""
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
        """Persist the config as a plain JSON file (matches existing CLI credential
        storage convention; see ``client/cli/v2/config_cmd.py``).
        """
        write_json_file(CHAT_CONFIG_FILE, self.model_dump_json(indent=2))
