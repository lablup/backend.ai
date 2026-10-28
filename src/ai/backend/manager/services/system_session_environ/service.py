from __future__ import annotations

from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironValueSource
from ai.backend.manager.repositories.system_session_environ.repository import (
    SystemSessionEnvironRepository,
)
from ai.backend.manager.services.system_session_environ.actions.create import (
    CreateSystemSessionEnvironAction,
    CreateSystemSessionEnvironActionResult,
)
from ai.backend.manager.services.system_session_environ.actions.public_list_value_sources import (
    PublicListSystemSessionEnvironValueSourcesAction,
    PublicListSystemSessionEnvironValueSourcesActionResult,
)

__all__ = ("SystemSessionEnvironService",)


class SystemSessionEnvironService:
    """The operations ops cannot back: the value sources are the manager's own list, not
    rows, and the create's spec carries a precondition."""

    _repository: SystemSessionEnvironRepository

    def __init__(self, repository: SystemSessionEnvironRepository) -> None:
        self._repository = repository

    async def create(
        self, action: CreateSystemSessionEnvironAction
    ) -> CreateSystemSessionEnvironActionResult:
        data = await self._repository.create(action.creator)
        return CreateSystemSessionEnvironActionResult(data=data)

    async def public_list_value_sources(
        self, action: PublicListSystemSessionEnvironValueSourcesAction
    ) -> PublicListSystemSessionEnvironValueSourcesActionResult:
        return PublicListSystemSessionEnvironValueSourcesActionResult(
            value_sources=list(SystemSessionEnvironValueSource)
        )
