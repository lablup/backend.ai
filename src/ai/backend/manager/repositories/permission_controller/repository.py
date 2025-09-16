import uuid
from typing import Optional

from ai.backend.common.metrics.metric import LayerType

from ...data.permission.role import (
    RoleCreateInput,
    RoleData,
    RoleDeleteInput,
    RoleUpdateInput,
    ScopePermissionCheckInput,
    SingleEntityPermissionCheckInput,
    UserRoleAssignmentInput,
)
from ...decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ...models.utils import ExtendedAsyncSAEngine
from .db_source import PermissionDBSource

# Layer-specific decorator for user repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.PERMISSION_CONTROL)


class PermissionControllerRepository:
    _db_source: PermissionDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = PermissionDBSource(db)

    @repository_decorator()
    async def create_role(self, data: RoleCreateInput) -> RoleData:
        """
        Create a new role in the database.

        Returns the ID of the created role.
        """
        role_row = await self._db_source.create_role(data)
        return role_row.to_data()

    @repository_decorator()
    async def update_role(self, data: RoleUpdateInput) -> RoleData:
        result = await self._db_source.update_role(data)
        return result.to_data()

    @repository_decorator()
    async def delete_role(self, data: RoleDeleteInput) -> RoleData:
        result = await self._db_source.delete_role(data)
        return result.to_data()

    @repository_decorator()
    async def assign_role(self, data: UserRoleAssignmentInput):
        result = await self._db_source.assign_role(data)
        return result.to_data()

    @repository_decorator()
    async def get_role(self, role_id: uuid.UUID) -> Optional[RoleData]:
        result = await self._db_source.get_role(role_id)
        return result.to_data() if result else None

    @repository_decorator()
    async def check_permission_of_entity(self, data: SingleEntityPermissionCheckInput) -> bool:
        target_object_id = data.target_object_id
        roles = await self._db_source.get_user_roles(data.user_id)
        associated_scopes = await self._db_source.get_entity_mapped_scopes(target_object_id)
        associated_scopes_set = set([row.parsed_scope_id() for row in associated_scopes])
        for role in roles:
            for object_perm in role.object_permission_rows:
                if object_perm.operation != data.operation:
                    continue
                if object_perm.object_id() == target_object_id:
                    return True

            for permission_group in role.permission_group_rows:
                if permission_group.parsed_scope_id() not in associated_scopes_set:
                    continue
                for permission in permission_group.permission_rows:
                    if permission.operation == data.operation:
                        return True
        return False

    @repository_decorator()
    async def check_permission_in_scope(self, data: ScopePermissionCheckInput) -> bool:
        target_scope_id = data.target_scope_id
        role_rows = await self._db_source.get_user_roles(data.user_id)
        for role in role_rows:
            for permission_group in role.permission_group_rows:
                if permission_group.parsed_scope_id() != target_scope_id:
                    continue
                for permission in permission_group.permission_rows:
                    if permission.operation == data.operation:
                        return True
        return False
