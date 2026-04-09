from __future__ import annotations

from ai.backend.manager.repositories.login_client_type.repository import (
    LoginClientTypeRepository,
)
from ai.backend.manager.services.login_client_type.actions.create import (
    CreateLoginClientTypeAction,
    CreateLoginClientTypeActionResult,
)
from ai.backend.manager.services.login_client_type.actions.delete import (
    DeleteLoginClientTypeAction,
    DeleteLoginClientTypeActionResult,
)
from ai.backend.manager.services.login_client_type.actions.get import (
    GetLoginClientTypeAction,
    GetLoginClientTypeActionResult,
)
from ai.backend.manager.services.login_client_type.actions.update import (
    UpdateLoginClientTypeAction,
    UpdateLoginClientTypeActionResult,
)

__all__ = ("LoginClientTypeService",)


class LoginClientTypeService:
    _repository: LoginClientTypeRepository

    def __init__(self, repository: LoginClientTypeRepository) -> None:
        self._repository = repository

    async def create(
        self, action: CreateLoginClientTypeAction
    ) -> CreateLoginClientTypeActionResult:
        data = await self._repository.create(action.creator)
        return CreateLoginClientTypeActionResult(login_client_type=data)

    async def get(self, action: GetLoginClientTypeAction) -> GetLoginClientTypeActionResult:
        data = await self._repository.get_by_id(action.id)
        return GetLoginClientTypeActionResult(login_client_type=data)

    async def update(
        self, action: UpdateLoginClientTypeAction
    ) -> UpdateLoginClientTypeActionResult:
        data = await self._repository.update(action.updater)
        return UpdateLoginClientTypeActionResult(login_client_type=data)

    async def delete(
        self, action: DeleteLoginClientTypeAction
    ) -> DeleteLoginClientTypeActionResult:
        data = await self._repository.delete(action.id)
        return DeleteLoginClientTypeActionResult(login_client_type=data)
