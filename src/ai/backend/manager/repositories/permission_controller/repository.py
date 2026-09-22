from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.permission.permission import (
    PermissionData,
)
from ai.backend.manager.data.permission.role import (
    AssignedUserListResult,
    BulkRoleAssignmentResultData,
    BulkRolePermissionReplaceResultData,
    BulkRoleRevocationResultData,
    BulkUserRoleRevocationInput,
    RoleData,
    RoleDetailData,
    RoleRevocationResult,
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.permission.purgers import RolePermissionPurger
from ai.backend.manager.models.rbac_models.permission.updaters import RolePermissionUpdater
from ai.backend.manager.models.rbac_models.role.searchable_fields import (
    RoleSearchableFields,
)
from ai.backend.manager.models.rbac_models.user_role.searchable_fields import (
    RoleAssignmentSearchableFields,
)
from ai.backend.manager.models.rbac_models.user_role.searchers import RoleAssignmentSearcher
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.permission import PermissionEntry
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

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
    async def create_permission(
        self,
        role_id: RoleID,
        creator: RolePermissionCreator,
    ) -> PermissionData:
        """
        Create a new permission in the database.

        Returns the created permission data.
        """
        return await self._db_source.create_permission(role_id, creator)

    @permission_controller_repository_resilience.apply()
    async def delete_permission(
        self,
        purger: RolePermissionPurger,
    ) -> PermissionData:
        """
        Delete a permission from the database.

        Returns the deleted permission data.

        Raises:
            PermissionNotFound: If permission does not exist.
        """
        return await self._db_source.delete_permission(purger)

    @permission_controller_repository_resilience.apply()
    async def update_permission(
        self,
        updater: RolePermissionUpdater,
    ) -> PermissionData:
        """
        Update a permission in the database.

        Returns the updated permission data.

        Raises:
            PermissionNotFound: If permission does not exist.
        """
        return await self._db_source.update_permission(updater)

    @permission_controller_repository_resilience.apply()
    async def replace_role_permissions(
        self,
        role_id: RoleID,
        entries: Sequence[PermissionEntry],
    ) -> BulkRolePermissionReplaceResultData:
        successes = await self._db_source.replace_role_permissions(role_id=role_id, entries=entries)
        return BulkRolePermissionReplaceResultData(role_id=role_id, successes=successes)

    @permission_controller_repository_resilience.apply()
    async def assign_role(self, data: UserRoleAssignmentInput) -> UserRoleAssignmentData:
        result = await self._db_source.assign_role(data)
        return RoleAssignmentSearchableFields.own.to_assignment_data(result)

    @permission_controller_repository_resilience.apply()
    async def revoke_role(self, data: UserRoleRevocationInput) -> RoleRevocationResult:
        return await self._db_source.revoke_role(data)

    @permission_controller_repository_resilience.apply()
    async def bulk_assign_role(
        self,
        role_id: RoleID,
        user_ids: Sequence[UserID],
        granted_by: UserID | None = None,
    ) -> BulkRoleAssignmentResultData:
        rows = await self._db_source.bulk_assign_role(role_id, user_ids, granted_by)
        return BulkRoleAssignmentResultData(
            successes=[RoleAssignmentSearchableFields.own.to_assignment_data(row) for row in rows]
        )

    @permission_controller_repository_resilience.apply()
    async def bulk_revoke_role(
        self, data: BulkUserRoleRevocationInput
    ) -> BulkRoleRevocationResultData:
        return await self._db_source.bulk_revoke_role(data)

    @permission_controller_repository_resilience.apply()
    async def get_role(self, role_id: uuid.UUID) -> RoleData | None:
        result = await self._db_source.get_role(role_id)
        return RoleSearchableFields.own.to_data(result) if result else None

    @permission_controller_repository_resilience.apply()
    async def get_role_with_permissions(self, role_id: uuid.UUID) -> RoleDetailData:
        """Get role with all permission details (without users)."""
        result = await self._db_source.get_role_with_permissions(role_id)
        return RoleSearchableFields.own.to_detail_data(result)

    @permission_controller_repository_resilience.apply()
    async def search_role_assignments_in_global(
        self,
        searcher: RoleAssignmentSearcher,
    ) -> AssignedUserListResult:
        """Search every assignment row, with no scope filter."""
        return await self._db_source.search_role_assignments_in_global(searcher)

    @permission_controller_repository_resilience.apply()
    async def search_role_assignments_in_scope(
        self,
        scopes: Sequence[OperationScope],
        searcher: RoleAssignmentSearcher,
    ) -> AssignedUserListResult:
        """Search the assignment rows the named scopes reach, combined with OR."""
        return await self._db_source.search_role_assignments_in_scope(
            scopes=scopes, searcher=searcher
        )
