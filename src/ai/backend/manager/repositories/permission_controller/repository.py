from __future__ import annotations

import uuid
from collections.abc import Mapping

from ai.backend.common.data.permission.types import GLOBAL_SCOPE_ID, OperationType
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.permission.entity import ElementAssociationListResult, EntityListResult
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.object_permission import (
    ObjectPermissionData,
    ObjectPermissionListResult,
)
from ai.backend.manager.data.permission.permission import (
    PermissionData,
    PermissionListResult,
)
from ai.backend.manager.data.permission.role import (
    AssignedUserListResult,
    BatchEntityPermissionCheckInput,
    RoleData,
    RoleDetailData,
    RoleListResult,
    RolePermissionsUpdateInput,
    ScopePermissionCheckInput,
    SingleEntityPermissionCheckInput,
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
    UserRoleRevocationData,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.types import (
    RBACElementRef,
    ScopeData,
    ScopeListResult,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.types import (
    ObjectPermissionSearchScope,
    PermissionSearchScope,
)

from .db_source.db_source import CreateRoleInput, PermissionDBSource

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
    async def create_role(self, input_data: CreateRoleInput) -> RoleData:
        """
        Create a new role in the database.

        Returns the created role data.
        """
        role_row = await self._db_source.create_role(input_data)
        return role_row.to_data()

    @permission_controller_repository_resilience.apply()
    async def create_permission(
        self,
        creator: Creator[PermissionRow],
    ) -> PermissionData:
        """
        Create a new permission in the database.

        Returns the created permission data.
        """
        row = await self._db_source.create_permission(creator)
        return row.to_data()

    @permission_controller_repository_resilience.apply()
    async def delete_permission(
        self,
        purger: Purger[PermissionRow],
    ) -> PermissionData:
        """
        Delete a permission from the database.

        Returns the deleted permission data.

        Raises:
            ObjectNotFound: If permission does not exist.
        """
        row = await self._db_source.delete_permission(purger)
        return row.to_data()

    @permission_controller_repository_resilience.apply()
    async def create_object_permission(
        self,
        creator: Creator[ObjectPermissionRow],
    ) -> ObjectPermissionData:
        """
        Create a new object permission in the database.

        Returns the created object permission data.
        """
        row = await self._db_source.create_object_permission(creator)
        return row.to_data()

    @permission_controller_repository_resilience.apply()
    async def delete_object_permission(
        self,
        purger: Purger[ObjectPermissionRow],
    ) -> ObjectPermissionData | None:
        """
        Delete an object permission from the database.

        Returns the deleted object permission data, or None if not found.
        """
        row = await self._db_source.delete_object_permission(purger)
        return row.to_data() if row else None

    @permission_controller_repository_resilience.apply()
    async def update_role(self, updater: Updater[RoleRow]) -> RoleData:
        result = await self._db_source.update_role(updater)
        return result.to_data()

    @permission_controller_repository_resilience.apply()
    async def update_role_permissions(
        self, input_data: RolePermissionsUpdateInput
    ) -> RoleDetailData:
        """Update role permissions using batch update."""
        result = await self._db_source.update_role_permissions(input_data=input_data)
        return result.to_detail_data_without_users()

    @permission_controller_repository_resilience.apply()
    async def delete_role(self, updater: Updater[RoleRow]) -> RoleData:
        result = await self._db_source.delete_role(updater)
        return result.to_data()

    @permission_controller_repository_resilience.apply()
    async def purge_role(self, purger: Purger[RoleRow]) -> RoleData:
        result = await self._db_source.purge_role(purger)
        return result.to_data()

    @permission_controller_repository_resilience.apply()
    async def assign_role(self, data: UserRoleAssignmentInput) -> UserRoleAssignmentData:
        result = await self._db_source.assign_role(data)
        return result.to_data()

    @permission_controller_repository_resilience.apply()
    async def revoke_role(self, data: UserRoleRevocationInput) -> UserRoleRevocationData:
        user_role_id = await self._db_source.revoke_role(data)
        return UserRoleRevocationData(
            user_role_id=user_role_id, user_id=data.user_id, role_id=data.role_id
        )

    @permission_controller_repository_resilience.apply()
    async def get_role(self, role_id: uuid.UUID) -> RoleData | None:
        result = await self._db_source.get_role(role_id)
        return result.to_data() if result else None

    @permission_controller_repository_resilience.apply()
    async def check_permission_of_entity(self, data: SingleEntityPermissionCheckInput) -> bool:
        target_object_id = data.target_object_id
        roles = await self._db_source.get_user_roles(data.user_id)
        for role in roles:
            for object_perm in role.object_permission_rows:
                if object_perm.operation != data.operation:
                    continue
                if object_perm.object_id() == target_object_id:
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
    async def search_permissions(
        self,
        querier: BatchQuerier,
        scope: PermissionSearchScope | None = None,
    ) -> PermissionListResult:
        """Searches permissions with pagination and filtering."""
        return await self._db_source.search_permissions(querier=querier, scope=scope)

    @permission_controller_repository_resilience.apply()
    async def search_object_permissions(
        self,
        querier: BatchQuerier,
        scope: ObjectPermissionSearchScope | None = None,
    ) -> ObjectPermissionListResult:
        """Searches object permissions with pagination and filtering."""
        return await self._db_source.search_object_permissions(querier=querier, scope=scope)

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

    def _get_global_scope(self) -> ScopeListResult:
        """Get the global scope as a static result."""
        return ScopeListResult(
            items=[
                ScopeData(
                    id=ScopeId(scope_type=ScopeType.GLOBAL, scope_id=GLOBAL_SCOPE_ID),
                    name=GLOBAL_SCOPE_ID,
                )
            ],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

    @permission_controller_repository_resilience.apply()
    async def search_scopes(
        self,
        scope_type: ScopeType,
        querier: BatchQuerier,
    ) -> ScopeListResult:
        """Search scopes based on scope type.

        Args:
            scope_type: The type of scope to search.
            querier: BatchQuerier with conditions, orders, and pagination.

        Returns:
            ScopeListResult with matching scopes.
        """
        match scope_type:
            case ScopeType.GLOBAL:
                return self._get_global_scope()
            case ScopeType.DOMAIN:
                return await self._db_source.search_domain_scopes(querier)
            case ScopeType.PROJECT:
                return await self._db_source.search_project_scopes(querier)
            case ScopeType.USER:
                return await self._db_source.search_user_scopes(querier)
            case _:
                raise NotImplementedError(
                    "This function will be deprecated and new repository functions will be implemented for each scope"
                )

    @permission_controller_repository_resilience.apply()
    async def search_entities(
        self,
        querier: BatchQuerier,
    ) -> EntityListResult:
        """Search entities within a scope.

        Args:
            querier: BatchQuerier with scope conditions and pagination settings.

        Returns:
            EntityListResult with matching entities.
        """
        return await self._db_source.search_entities_in_scope(querier)

    @permission_controller_repository_resilience.apply()
    async def search_element_associations(
        self,
        querier: BatchQuerier,
    ) -> ElementAssociationListResult:
        """Search element associations (full association rows) within a scope.

        Args:
            querier: BatchQuerier with scope conditions and pagination settings.

        Returns:
            ElementAssociationListResult with full association row data.
        """
        return await self._db_source.search_element_associations_in_scope(querier)

    @permission_controller_repository_resilience.apply()
    async def check_permission_with_scope_chain(
        self,
        user_id: uuid.UUID,
        target_element_ref: RBACElementRef,
        operation: OperationType,
    ) -> bool:
        """CTE-based permission check that traverses the scope chain via AUTO edges only.

        Walks the association_scopes_entities hierarchy upward from the target
        entity, checking if the user has the requested operation at any ancestor
        scope. REF edges are not traversed.
        """
        return await self._db_source.check_permission_with_scope_chain(
            user_id=user_id,
            target_element_ref=target_element_ref,
            operation=operation,
        )
