from __future__ import annotations

from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironValueSource
from ai.backend.manager.services.system_session_environ.actions.public_list_value_sources import (
    PublicListSystemSessionEnvironValueSourcesAction,
    PublicListSystemSessionEnvironValueSourcesActionResult,
)

__all__ = ("SystemSessionEnvironService",)


class SystemSessionEnvironService:
    """The operations ops cannot back: the value sources are the manager's own list, not rows."""

    async def public_list_value_sources(
        self, action: PublicListSystemSessionEnvironValueSourcesAction
    ) -> PublicListSystemSessionEnvironValueSourcesActionResult:
        return PublicListSystemSessionEnvironValueSourcesActionResult(
            value_sources=list(SystemSessionEnvironValueSource)
        )
