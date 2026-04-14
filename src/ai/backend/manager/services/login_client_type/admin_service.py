from __future__ import annotations

from ai.backend.manager.repositories.login_client_type.admin_repository import (
    LoginClientTypeAdminRepository,
)
from ai.backend.manager.services.login_client_type.actions.create import (
    CreateLoginClientTypeAction,
    CreateLoginClientTypeActionResult,
)
from ai.backend.manager.services.login_client_type.actions.delete import (
    DeleteLoginClientTypeAction,
    DeleteLoginClientTypeActionResult,
)
from ai.backend.manager.services.login_client_type.actions.update import (
    UpdateLoginClientTypeAction,
    UpdateLoginClientTypeActionResult,
)

__all__ = ("LoginClientTypeAdminService",)


class LoginClientTypeAdminService:
    _admin_repository: LoginClientTypeAdminRepository

    def __init__(self, admin_repository: LoginClientTypeAdminRepository) -> None:
        self._admin_repository = admin_repository

    async def create(
        self, action: CreateLoginClientTypeAction
    ) -> CreateLoginClientTypeActionResult:
        data = await self._admin_repository.create(action.creator)
        return CreateLoginClientTypeActionResult(login_client_type=data)

    async def update(
        self, action: UpdateLoginClientTypeAction
    ) -> UpdateLoginClientTypeActionResult:
        data = await self._admin_repository.update(action.updater)
        return UpdateLoginClientTypeActionResult(login_client_type=data)

    async def delete(
        self, action: DeleteLoginClientTypeAction
    ) -> DeleteLoginClientTypeActionResult:
        data = await self._admin_repository.delete(action.id)
        return DeleteLoginClientTypeActionResult(login_client_type=data)
