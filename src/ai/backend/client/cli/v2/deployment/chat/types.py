"""Type definitions for ``./bai deployment chat`` storage."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeploymentChatCacheEntry(BaseModel):
    """One deployment's auto-managed endpoint metadata."""

    endpoint_url: str
    default_model: str | None = None
    last_synced_at: datetime


class DeploymentChatCache(BaseModel):
    """In-memory representation of the chat cache file."""

    deployments: dict[UUID, DeploymentChatCacheEntry] = Field(default_factory=dict)

    def get(self, deployment_id: UUID) -> DeploymentChatCacheEntry | None:
        return self.deployments.get(deployment_id)

    def set(self, deployment_id: UUID, entry: DeploymentChatCacheEntry) -> None:
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
