"""Display helpers for ``./bai deployment chat-config show``."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.cli.v2.deployment.chat.types import DeploymentChatCacheEntry


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
        token_display: str,
    ) -> None:
        print(f"deployment_id : {deployment_id}")
        for line in cls.entry_lines(entry):
            print(line)
        print(f"api_key       : {token_display}")
