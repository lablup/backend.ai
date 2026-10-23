from __future__ import annotations

from ai.backend.manager.repositories.system_session_environ.repository import (
    SystemSessionEnvironRepository,
)
from ai.backend.manager.services.system_session_environ.actions.global_resolve import (
    GlobalResolveSystemSessionEnvironAction,
    GlobalResolveSystemSessionEnvironActionResult,
)

__all__ = ("SystemSessionEnvironService",)


class SystemSessionEnvironService:
    _repository: SystemSessionEnvironRepository

    def __init__(self, repository: SystemSessionEnvironRepository) -> None:
        self._repository = repository

    async def global_resolve(
        self, action: GlobalResolveSystemSessionEnvironAction
    ) -> GlobalResolveSystemSessionEnvironActionResult:
        effective_rows = await self._repository.resolve_rows(action.domain_id, action.project_id)
        return GlobalResolveSystemSessionEnvironActionResult(effective_rows=effective_rows)
