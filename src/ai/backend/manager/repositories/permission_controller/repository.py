import uuid
from collections.abc import Mapping
from typing import Optional

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience

from ...data.permission.id import ObjectId
from ...data.permission.role import (
    AssignedUserListResult,
    BatchEntityPermissionCheckInput,
    RoleCreateInput,
    RoleData,
    RoleDeleteInput,
    RoleDetailData,
    RoleListResult,
    RoleUpdateInput,
    ScopePermissionCheckInput,
    SingleEntityPermissionCheckInput,
    UserRoleAssignmentInput,
)
from ...models.utils import ExtendedAsyncSAEngine
from ...repositories.base import BatchQuerier
from .db_source.db_source import PermissionDBSource

permission_controller_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY, layer=LayerType.PERMISSION_CONTROLLER_REPOSITORY
            )
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class PermissionControllerRepository:
    _db_source: PermissionDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = PermissionDBSource(db)

    @permission_controller_repository_resilience.apply()
    async def create_role(self, data: RoleCreateInput) -> RoleData:
        """
        Create a new role in the database.

        Returns the ID of the created role.
        """
        role_row = await self._db_source.create_role(data)
        return role_row.to_data()

    @permission_controller_repository_resilience.apply()
    async def update_role(self, data: RoleUpdateInput) -> RoleData:
        result = await self._db_source.update_role(data)
        return result.to_data()

    @permission_controller_repository_resilience.apply()
    async def delete_role(self, data: RoleDeleteInput) -> RoleData:
        result = await self._db_source.delete_role(data)
        return result.to_data()

    @permission_controller_repository_resilience.apply()
    async def assign_role(self, data: UserRoleAssignmentInput):
        result = await self._db_source.assign_role(data)
        return result.to_data()

    @permission_controller_repository_resilience.apply()
    async def get_role(self, role_id: uuid.UUID) -> Optional[RoleData]:
        result = await self._db_source.get_role(role_id)
        return result.to_data() if result else None

    @permission_controller_repository_resilience.apply()
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

    @permission_controller_repository_resilience.apply()
    async def check_permission_in_scope(self, data: ScopePermissionCheckInput) -> bool:
        return await self._db_source.check_scope_permission_exist(
            data.user_id, data.target_scope_id, data.operation
        )

    @permission_controller_repository_resilience.apply()
    async def check_permission_of_entities(
        self,
        data: BatchEntityPermissionCheckInput,
    ) -> Mapping[ObjectId, bool]:
        """
        Check if the user has the requested operation permission on the given entity IDs.
        Returns a mapping of entity ID to a boolean indicating permission.
        """
        return await self._db_source.check_batch_object_permission_exist(
            data.user_id, data.target_object_ids, data.operation
        )

    @permission_controller_repository_resilience.apply()
    async def search_roles(
        self,
        querier: BatchQuerier,
    ) -> RoleListResult:
        """Searches roles with pagination and filtering."""
        return await self._db_source.search_roles(querier=querier)

    @permission_controller_repository_resilience.apply()
    async def get_role_with_permissions(self, role_id: uuid.UUID) -> RoleDetailData:
        """Get role with all permission details (without users)."""
        result = await self._db_source.get_role_with_permissions(role_id)
        return result.to_detail_data_without_users()

    @permission_controller_repository_resilience.apply()
    async def search_users_assigned_to_role(
        self,
        role_id: uuid.UUID,
        querier: BatchQuerier,
    ) -> AssignedUserListResult:
        """Searches users assigned to a specific role with pagination and filtering."""
        return await self._db_source.search_users_assigned_to_role(
            role_id=role_id,
            querier=querier,
        )
