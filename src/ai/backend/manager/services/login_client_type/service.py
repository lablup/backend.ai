from __future__ import annotations

from ai.backend.common.exception import InvalidAPIParameters
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
from ai.backend.manager.services.login_client_type.actions.list import (
    ListLoginClientTypesAction,
    ListLoginClientTypesActionResult,
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
        data = await self._repository.create(action.name, action.description)
        return CreateLoginClientTypeActionResult(login_client_type=data)

    async def get(self, action: GetLoginClientTypeAction) -> GetLoginClientTypeActionResult:
        if action.id is not None:
            data = await self._repository.get_by_id(action.id)
        elif action.name is not None:
            data = await self._repository.get_by_name(action.name)
        else:
            raise InvalidAPIParameters("One of (`id` or `name`) must be provided.")
        return GetLoginClientTypeActionResult(login_client_type=data)

    async def list_all(
        self, action: ListLoginClientTypesAction
    ) -> ListLoginClientTypesActionResult:
        del action
        items = await self._repository.list_all()
        return ListLoginClientTypesActionResult(login_client_types=items)

    async def update(
        self, action: UpdateLoginClientTypeAction
    ) -> UpdateLoginClientTypeActionResult:
        data = await self._repository.update(
            action.id,
            name=action.name,
            description_set=action.description_set,
            description=action.description,
        )
        return UpdateLoginClientTypeActionResult(login_client_type=data)

    async def delete(
        self, action: DeleteLoginClientTypeAction
    ) -> DeleteLoginClientTypeActionResult:
        data = await self._repository.delete(action.id)
        return DeleteLoginClientTypeActionResult(login_client_type=data)
