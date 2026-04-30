"""Display helpers for ``./bai deployment chat-config show``."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.cli.v2.deployment.chat.types import DeploymentChatConfigEntry


def mask_token(token: str | None) -> str:
    """Render a stored token as a fixed placeholder for diagnostic display.

    The placeholder is length-independent so the masked output never leaks the
    token's length, prefix, or suffix.
    """
    if token is None:
        return "<unset>"
    return "********"


class DeploymentChatFormatter:
    """Formatting helpers for the user-managed chat config entry.

    Formatting and rendering live here rather than on
    :class:`DeploymentChatConfigEntry` so the data model stays free of
    presentation concerns.
    """

    @classmethod
    def print_config(
        cls,
        deployment_id: UUID,
        entry: DeploymentChatConfigEntry,
    ) -> None:
        print(f"deployment_id : {deployment_id}")
        print(f"model         : {entry.model or '-'}")
        print(f"token         : {mask_token(entry.token)}")
