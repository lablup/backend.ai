import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.permission_contoller.actions.assign_role import (
    AssignRoleAction,
    AssignRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.create_role import (
    CreateRoleAction,
    CreateRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.delete_role import (
    DeleteRoleAction,
    DeleteRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.update_role import (
    UpdateRoleAction,
    UpdateRoleActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PermissionControllerService:
    _repository: PermissionControllerRepository

    def __init__(self, repository: PermissionControllerRepository) -> None:
        self._repository = repository

    async def create_role(self, action: CreateRoleAction) -> CreateRoleActionResult:
        """
        Creates a new role in the repository.
        """
        result = await self._repository.create_role(action.input)
        return CreateRoleActionResult(
            data=result,
            success=True,
        )

    async def update_role(self, action: UpdateRoleAction) -> UpdateRoleActionResult:
        """
        Updates an existing role in the repository.
        If the role does not exist, it returns a result indicating failure.
        """
        try:
            result = await self._repository.update_role(action.input)
        except ObjectNotFound:
            return UpdateRoleActionResult(data=None, success=False)
        return UpdateRoleActionResult(
            data=result,
            success=True,
        )

    async def delete_role(self, action: DeleteRoleAction) -> DeleteRoleActionResult:
        """
        Deletes a role from the repository. It marks the role as deleted.
        If the role does not exist, it returns a result indicating failure.
        """
        try:
            _ = await self._repository.delete_role(action.input)
        except ObjectNotFound:
            return DeleteRoleActionResult(success=False)
        return DeleteRoleActionResult(success=True)

    async def assign_role(self, action: AssignRoleAction) -> AssignRoleActionResult:
        """
        Assigns a role to a user.
        """
        data = await self._repository.assign_role(action.input)

        return AssignRoleActionResult(success=True, data=data)
