"""Type definitions for ``./bai deployment chat`` storage."""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Annotated, Self

from pydantic import Field

from ai.backend.client.cli.v2.deployment.chat.utils import (
    CHAT_CACHE_FILE,
    CHAT_CONFIG_FILE,
    CHAT_HISTORY_FILE,
    read_json_file,
    write_json_file,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.types import BackendAISchema

CACHE_ENTRY_TTL = timedelta(hours=24)
"""Endpoint cache entries older than this are treated as a cache miss."""

DEFAULT_CHAT_HISTORY_LIMIT = 10
"""Default number of past messages forwarded as context on each ``chat`` call.

Mirrors the typical 5-turn rolling window of OpenAI-compatible chat UIs.
Override per-call with ``--history-limit``; setting it to 0 disables context.
"""

MAX_PERSISTED_HISTORY_MESSAGES = 100
"""Hard cap on messages kept in ``history.json`` per deployment.

The file holds plain text; capping it keeps disk usage bounded even when the
user never runs ``chat-history clear``. Older messages are dropped FIFO.
"""


class DeploymentChatCacheEntry(BackendAISchema):
    """One deployment's auto-managed endpoint metadata."""

    endpoint_url: str
    default_model: str | None = None
    last_synced_at: datetime

    def is_expired(self, *, now: datetime, ttl: timedelta = CACHE_ENTRY_TTL) -> bool:
        """Whether this entry is older than the cache TTL window."""
        return now - self.last_synced_at >= ttl


class DeploymentChatCache(BackendAISchema):
    """In-memory representation of the chat cache file."""

    deployments: dict[DeploymentID, DeploymentChatCacheEntry] = Field(default_factory=dict)

    def get(self, deployment_id: DeploymentID) -> DeploymentChatCacheEntry | None:
        return self.deployments.get(deployment_id)

    def set(self, deployment_id: DeploymentID, entry: DeploymentChatCacheEntry) -> None:
        self.deployments[deployment_id] = entry

    def delete(self, deployment_id: DeploymentID) -> bool:
        """Remove the cache entry for ``deployment_id``; return True when an entry was removed."""
        return self.deployments.pop(deployment_id, None) is not None

    @classmethod
    def load(cls) -> Self:
        """Load the chat cache; return an empty cache when the file is absent or unreadable."""
        raw = read_json_file(CHAT_CACHE_FILE)
        if raw is None:
            return cls()
        try:
            return cls.model_validate(raw)
        except BackendAISchemaValidationFailed:
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


class DeploymentChatConfigEntry(BackendAISchema):
    """One deployment's user-managed state.

    ``model`` holds the user's explicit ``--model`` choice for a deployment;
    it takes precedence over :attr:`DeploymentChatCacheEntry.default_model`
    (which is the value the CLI auto-derived from ``GET /v1/models``).
    """

    token: str | None = None
    model: str | None = None

    def is_empty(self) -> bool:
        return self.token is None and self.model is None


class DeploymentChatConfig(BackendAISchema):
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

    def clear_token(self, deployment_id: DeploymentID) -> bool:
        """Null the token field for ``deployment_id``; return True when a token was cleared.

        Drops the entry entirely if both ``token`` and ``model`` end up unset.
        """
        entry = self.deployments.get(deployment_id)
        if entry is None or entry.token is None:
            return False
        entry.token = None
        if entry.is_empty():
            del self.deployments[deployment_id]
        return True

    def clear_model(self, deployment_id: DeploymentID) -> bool:
        """Null the model field for ``deployment_id``; return True when a model was cleared.

        Drops the entry entirely if both ``token`` and ``model`` end up unset.
        """
        entry = self.deployments.get(deployment_id)
        if entry is None or entry.model is None:
            return False
        entry.model = None
        if entry.is_empty():
            del self.deployments[deployment_id]
        return True

    def delete(self, deployment_id: DeploymentID) -> bool:
        """Remove the config entry for ``deployment_id``; return True when an entry was removed."""
        return self.deployments.pop(deployment_id, None) is not None

    @classmethod
    def load(cls) -> Self:
        """Load the chat config; return an empty config when the file is absent or unreadable."""
        raw = read_json_file(CHAT_CONFIG_FILE)
        if raw is None:
            return cls()
        try:
            return cls.model_validate(raw)
        except BackendAISchemaValidationFailed:
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


class ChatMessage(BackendAISchema):
    """One persisted user/assistant turn.

    ``created_at`` is local-only metadata for ``chat-history show``; it is
    stripped before the message is replayed into the chat-completions request
    body (the wire format is just ``{role, content}``).
    """

    role: str
    content: str
    created_at: datetime


class DeploymentChatHistory(BackendAISchema):
    """Per-deployment rolling chat transcripts.

    Stored separately from the cache (auto-managed endpoint metadata) and
    config (user-managed token/model) so that clearing one does not affect
    the others. The transcripts are FIFO-truncated at
    :data:`MAX_PERSISTED_HISTORY_MESSAGES` to bound disk usage.
    """

    deployments: dict[DeploymentID, list[ChatMessage]] = Field(default_factory=dict)

    def get(self, deployment_id: DeploymentID) -> list[ChatMessage] | None:
        return self.deployments.get(deployment_id)

    def slice(self, deployment_id: DeploymentID, limit: int) -> list[ChatMessage]:
        """Return the last ``limit`` turns of the transcript for replay as request context."""
        if limit <= 0:
            return []
        messages = self.deployments.get(deployment_id)
        if not messages:
            return []
        return messages[-limit:]

    def append(
        self,
        deployment_id: DeploymentID,
        role: str,
        content: str,
        *,
        created_at: datetime,
        max_persisted: int = MAX_PERSISTED_HISTORY_MESSAGES,
    ) -> None:
        """Append one turn and FIFO-truncate to keep the file bounded."""
        messages = self.deployments.setdefault(deployment_id, [])
        messages.append(ChatMessage(role=role, content=content, created_at=created_at))
        overflow = len(messages) - max_persisted
        if overflow > 0:
            del messages[:overflow]

    def clear(self, deployment_id: DeploymentID) -> bool:
        return self.deployments.pop(deployment_id, None) is not None

    @classmethod
    def load(cls) -> Self:
        """Load the chat history; return an empty history when the file is absent or unreadable."""
        raw = read_json_file(CHAT_HISTORY_FILE)
        if raw is None:
            return cls()
        try:
            return cls.model_validate(raw)
        except BackendAISchemaValidationFailed:
            print(
                f"WARNING: {CHAT_HISTORY_FILE} is in an invalid format and was ignored.",
                file=sys.stderr,
            )
            return cls()

    def save(self) -> None:
        """Persist the history as a plain JSON file (matches existing CLI credential
        storage convention; see ``client/cli/v2/config_cmd.py``).
        """
        write_json_file(CHAT_HISTORY_FILE, self.model_dump_json(indent=2))
