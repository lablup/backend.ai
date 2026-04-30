"""Display helpers for ``./bai deployment chat-config show`` / ``chat-cache show``."""

from __future__ import annotations

from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCacheEntry,
    DeploymentChatConfigEntry,
)
from ai.backend.common.identifier.deployment import DeploymentID


def mask_token(token: str | None) -> str:
    """Render a stored token as a fixed placeholder for diagnostic display.

    The placeholder is length-independent so the masked output never leaks the
    token's length, prefix, or suffix.
    """
    if token is None:
        return "<unset>"
    return "********"


class DeploymentChatFormatter:
    """Formatting helpers for the chat config and cache entries.

    Formatting and rendering live here rather than on the data classes so
    the data model stays free of presentation concerns.
    """

    @classmethod
    def print_config(
        cls,
        deployment_id: DeploymentID,
        entry: DeploymentChatConfigEntry,
    ) -> None:
        print(f"deployment_id : {deployment_id}")
        print(f"model         : {entry.model or '-'}")
        print(f"token         : {mask_token(entry.token)}")

    @classmethod
    def print_cache(
        cls,
        deployment_id: DeploymentID,
        entry: DeploymentChatCacheEntry,
    ) -> None:
        print(f"deployment_id : {deployment_id}")
        print(f"endpoint_url  : {entry.endpoint_url}")
        print(f"default_model : {entry.default_model or '-'}")
        print(f"last_synced_at: {entry.last_synced_at.isoformat()}")
