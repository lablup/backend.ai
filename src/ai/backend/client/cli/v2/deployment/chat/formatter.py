"""Display helpers for ``./bai deployment chat-config show``."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.cli.v2.deployment.chat.types import DeploymentChatCacheEntry

TOKEN_PLACEHOLDER = "********"


def mask_token(token: str | None) -> str:
    """Render a stored token as a fixed placeholder for diagnostic display.

    The placeholder is length-independent so the masked output never leaks the
    token's length, prefix, or suffix.
    """
    if token is None:
        return "<unset>"
    return TOKEN_PLACEHOLDER


class DeploymentChatFormatter:
    """Formatting helpers for chat cache entries.

    Formatting and rendering live here rather than on
    :class:`DeploymentChatCacheEntry` so the data model stays free of
    presentation concerns.
    """

    @staticmethod
    def entry_lines(entry: DeploymentChatCacheEntry | None) -> list[str]:
        if entry is None:
            return [
                "endpoint_url  : -",
                "default_model : -",
                "last_synced_at: -",
            ]
        return [
            f"endpoint_url  : {entry.endpoint_url}",
            f"default_model : {entry.default_model or '-'}",
            f"last_synced_at: {entry.last_synced_at.isoformat()}",
        ]

    @classmethod
    def print_summary(
        cls,
        deployment_id: UUID,
        entry: DeploymentChatCacheEntry | None,
        token: str | None,
    ) -> None:
        print(f"deployment_id : {deployment_id}")
        for line in cls.entry_lines(entry):
            print(line)
        print(f"token         : {mask_token(token)}")
