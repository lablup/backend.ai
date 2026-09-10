from __future__ import annotations

import uuid
from collections.abc import Collection, Mapping, Sequence

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission, RBACElementType
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.permission.permission import (
    PermissionData,
    PermissionListResult,
)
from ai.backend.manager.data.permission.role import (
    AssignedUserListResult,
    BulkRoleAssignmentResultData,
    BulkRolePermissionReplaceResultData,
    BulkRoleRevocationResultData,
    BulkUserRoleRevocationInput,
    RoleData,
    RoleDetailData,
    RoleListResult,
    RoleRevocationResult,
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.types import (
    ScopeListResult,
)
from ai.backend.manager.data.permission.virtual_entity import (
    GovernCheckKey,
    OwnCheckKey,
)
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.permission.purgers import RolePermissionPurger
from ai.backend.manager.models.rbac_models.permission.scopes import PermissionOperationScope
from ai.backend.manager.models.rbac_models.permission.updaters import RolePermissionUpdater
from ai.backend.manager.models.rbac_models.role.scopes import ScopedRoleOperationScope
from ai.backend.manager.models.specs.permission import PermissionEntry
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.querier import BatchQuerier

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
            ObjectNotFound: If permission does not exist.
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
            ObjectNotFound: If permission does not exist.
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
        return result.to_data()

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
        return BulkRoleAssignmentResultData(successes=[row.to_data() for row in rows])

    @permission_controller_repository_resilience.apply()
    async def bulk_revoke_role(
        self, data: BulkUserRoleRevocationInput
    ) -> BulkRoleRevocationResultData:
        return await self._db_source.bulk_revoke_role(data)

    @permission_controller_repository_resilience.apply()
    async def get_role(self, role_id: uuid.UUID) -> RoleData | None:
        result = await self._db_source.get_role(role_id)
        return result.to_data() if result else None

    @permission_controller_repository_resilience.apply()
    async def search_roles(
        self,
        querier: BatchQuerier,
    ) -> RoleListResult:
        """Searches roles with pagination and filtering."""
        return await self._db_source.search_roles(querier=querier)

    @permission_controller_repository_resilience.apply()
    async def search_roles_in_scope(
        self,
        querier: BatchQuerier,
        scope: ScopedRoleOperationScope,
    ) -> RoleListResult:
        """Search roles registered in a project scope."""
        return await self._db_source.search_roles_in_scope(querier=querier, scope=scope)

    @permission_controller_repository_resilience.apply()
    async def search_permissions(
        self,
        querier: BatchQuerier,
        scope: PermissionOperationScope | None = None,
    ) -> PermissionListResult:
        """Searches permissions with pagination and filtering."""
        return await self._db_source.search_permissions(querier=querier, scope=scope)

    @permission_controller_repository_resilience.apply()
    async def get_role_with_permissions(self, role_id: uuid.UUID) -> RoleDetailData:
        """Get role with all permission details (without users)."""
        result = await self._db_source.get_role_with_permissions(role_id)
        return result.to_detail_data_without_users()

    @permission_controller_repository_resilience.apply()
    async def search_users_assigned_to_role(
        self,
        querier: BatchQuerier,
    ) -> AssignedUserListResult:
        """Searches users assigned to a specific role with pagination and filtering."""
        return await self._db_source.search_users_assigned_to_role(
            querier=querier,
        )

    @permission_controller_repository_resilience.apply()
    async def search_scopes(
        self,
        element_type: RBACElementType,
        querier: BatchQuerier,
    ) -> ScopeListResult:
        """Search scopes based on element type.

        Args:
            element_type: The RBAC element type of scope to search.
            querier: BatchQuerier with conditions, orders, and pagination.

        Returns:
            ScopeListResult with matching scopes.
        """
        match element_type:
            case RBACElementType.DOMAIN:
                return await self._db_source.search_domain_scopes(querier)
            case RBACElementType.PROJECT:
                return await self._db_source.search_project_scopes(querier)
            case RBACElementType.USER:
                return await self._db_source.search_user_scopes(querier)
            case _:
                raise NotImplementedError(
                    "This function will be deprecated and new repository functions will be implemented for each scope"
                )

    @permission_controller_repository_resilience.apply()
    async def owned_permissions(
        self,
        keys: Collection[OwnCheckKey],
    ) -> Mapping[OwnCheckKey, Permission]:
        """The bits each user holds on each entity through own and govern; a key
        nothing reaches maps to :attr:`Permission.NONE`."""
        return await self._db_source.owned_permissions(keys)

    @permission_controller_repository_resilience.apply()
    async def governed_permissions(
        self,
        keys: Collection[GovernCheckKey],
    ) -> Mapping[GovernCheckKey, Permission]:
        """The bits each user holds on the key's entity type within the key's scope;
        a key nothing reaches maps to :attr:`Permission.NONE`."""
        return await self._db_source.governed_permissions(keys)
