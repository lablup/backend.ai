from __future__ import annotations

from ai.backend.manager.repositories.login_client_type.repository import (
    LoginClientTypeRepository,
)
from ai.backend.manager.services.login_client_type.actions.get import (
    GetLoginClientTypeAction,
    GetLoginClientTypeActionResult,
)
from ai.backend.manager.services.login_client_type.actions.search import (
    SearchLoginClientTypesAction,
    SearchLoginClientTypesActionResult,
)

__all__ = ("LoginClientTypeService",)


class LoginClientTypeService:
    _repository: LoginClientTypeRepository

    def __init__(self, repository: LoginClientTypeRepository) -> None:
        self._repository = repository

    async def get(self, action: GetLoginClientTypeAction) -> GetLoginClientTypeActionResult:
        data = await self._repository.get_by_id(action.id)
        return GetLoginClientTypeActionResult(login_client_type=data)

    async def search(
        self, action: SearchLoginClientTypesAction
    ) -> SearchLoginClientTypesActionResult:
        """Search login client types with filtering, ordering, and pagination."""
        result = await self._repository.search(querier=action.querier)
        return SearchLoginClientTypesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
