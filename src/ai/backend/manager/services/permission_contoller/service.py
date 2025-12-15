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
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
    GetRoleDetailActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    SearchRolesAction,
    SearchRolesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_users_assigned_to_role import (
    SearchUsersAssignedToRoleAction,
    SearchUsersAssignedToRoleActionResult,
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

    async def get_role_detail(self, action: GetRoleDetailAction) -> GetRoleDetailActionResult:
        """Get role with all permission details and assigned users."""
        role_data = await self._repository.get_role_with_permissions(action.role_id)
        return GetRoleDetailActionResult(role=role_data)

    async def search_roles(self, action: SearchRolesAction) -> SearchRolesActionResult:
        """Search roles with pagination and filtering."""
        result = await self._repository.search_roles(action.querier)
        return SearchRolesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_users_assigned_to_role(
        self, action: SearchUsersAssignedToRoleAction
    ) -> SearchUsersAssignedToRoleActionResult:
        """Search users assigned to a specific role with pagination and filtering."""
        result = await self._repository.search_users_assigned_to_role(
            role_id=action.role_id,
            querier=action.querier,
        )
        return SearchUsersAssignedToRoleActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
