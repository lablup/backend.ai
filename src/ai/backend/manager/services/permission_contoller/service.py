import logging
from collections import defaultdict

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.permission.id import (
    ObjectId,
    ScopeId,
)
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
from ai.backend.manager.services.permission_contoller.actions.list_access import (
    ListAccessAction,
    ListAccessActionResult,
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

    async def list_access(self, action: ListAccessAction) -> ListAccessActionResult:
        """
        Lists the access permissions for a user based on their roles.
        It returns the allowed operations for both scope and object permissions.
        """
        roles = await self._repository.get_active_roles(action.user_id)

        scope_allowed_operations: defaultdict[ScopeId, set[str]] = defaultdict(set)
        object_allowed_operations: defaultdict[ObjectId, set[str]] = defaultdict(set)
        for role in roles:
            for scope_perm in role.scope_permissions:
                if scope_perm.operation != action.operation:
                    continue
                scope_allowed_operations[scope_perm.scope_id].add(scope_perm.operation)
            for object_perm in role.object_permissions:
                if object_perm.operation != action.operation:
                    continue
                object_allowed_operations[object_perm.object_id].add(object_perm.operation)
        return ListAccessActionResult(
            scope_allowed_operations=dict(scope_allowed_operations),
            object_allowed_operations=dict(object_allowed_operations),
        )
