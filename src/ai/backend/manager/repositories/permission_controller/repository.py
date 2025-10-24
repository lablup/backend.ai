import uuid
from collections.abc import Mapping
from typing import Optional, Self

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience

from ...data.permission.id import ObjectId
from ...data.permission.role import (
    BatchEntityPermissionCheckInput,
    RoleCreateInput,
    RoleData,
    RoleDeleteInput,
    RoleUpdateInput,
    ScopePermissionCheckInput,
    SingleEntityPermissionCheckInput,
    UserRoleAssignmentInput,
)
from ...models.utils import ExtendedAsyncSAEngine
from ..types import RepositoryArgs
from .db_source import PermissionDBSource

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

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            db=args.db,
        )

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
        """
        Check if the user has the requested operation permission on the given entity.
        Returns True if the permission exists, False otherwise.
        """
        return await self._db_source.check_object_permission_exist(
            data.user_id, data.target_object_id, data.operation
        )

    @permission_controller_repository_resilience.apply()
    async def check_permission_in_scope(self, data: ScopePermissionCheckInput) -> bool:
        """
        Check if the user has the requested operation permission in the given scope.
        Returns True if the permission exists, False otherwise.
        """
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
