"""Type definitions for ``./bai deployment chat`` storage."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeploymentChatCacheEntry(BaseModel):
    """One deployment's auto-managed endpoint metadata."""

    model_config = ConfigDict(frozen=True)

    endpoint_url: str
    default_model: str | None = None
    last_synced_at: datetime

    def format_summary(self) -> list[str]:
        return [
            f"endpoint_url  : {self.endpoint_url}",
            f"default_model : {self.default_model or '-'}",
            f"last_synced_at: {self.last_synced_at.isoformat()}",
        ]


class DeploymentChatCache(BaseModel):
    """In-memory representation of the chat cache file."""

    deployments: dict[UUID, DeploymentChatCacheEntry] = Field(default_factory=dict)

    def get(self, deployment_id: UUID) -> DeploymentChatCacheEntry | None:
        return self.deployments.get(deployment_id)

    def upsert(self, deployment_id: UUID, entry: DeploymentChatCacheEntry) -> None:
        self.deployments[deployment_id] = entry

    def remove(self, deployment_id: UUID) -> bool:
        return self.deployments.pop(deployment_id, None) is not None


class DeploymentChatConfig(BaseModel):
    """Per-deployment API key registry (user-managed)."""

    tokens: dict[UUID, str] = Field(default_factory=dict)

    def get_token(self, deployment_id: UUID) -> str | None:
        return self.tokens.get(deployment_id)

    def set_token(self, deployment_id: UUID, token: str) -> None:
        self.tokens[deployment_id] = token

    def clear_token(self, deployment_id: UUID) -> bool:
        return self.tokens.pop(deployment_id, None) is not None


class IncompatibleChatCacheError(Exception):
    """Raised when the on-disk cache file uses a newer schema than this build."""


class IncompatibleChatConfigError(Exception):
    """Raised when the on-disk config file uses a newer schema than this build."""
